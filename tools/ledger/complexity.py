"""An easy-first ordering over ledger function entries — the "what next" ranking.

The ledger is the queue (``docs/llm-harness-design.md`` → *Worklist*), but its natural
order is ``(module, addr)``, i.e. link order. Link order says nothing about *difficulty*:
the first pending function in ``main`` is the runtime initializer ``_init``, near the worst
possible place to start. This module supplies a difficulty key so a caller can order the
pending functions from easiest to hardest.

It is a **library**, not a CLI: the reconstruction loop (``tools/loop/run.py``) passes the key
to the worklist selector, and future manual-decomp tooling calls the same functions. The
scoring is deliberately **pure** — it decodes bytes handed to it and touches no filesystem, no
ledger, and no network — so it is trivially unit-testable and safe to call from anywhere. The
sole exception is :func:`load_text`, the one convenience that reads the reference image (the
same pure-Python path ``tools/nso/nso_extract.py`` uses, no Ghidra); every other function takes
bytes and returns values.

The metric (v3)
---------------
The gate can currently verify a **relocation-free leaf** cleanly; a function whose object
carries relocations needs the not-yet-built relocation-aware diff
(``tools/ledger/bytegate.py`` → *Scope*). Because this image's relocations all land in
``.data``/``.got`` (its ``.text`` carries none), "relocation-free" cannot be read off the
image's relocation tables — it is a property of what the *reconstruction* will need. Three
cheap, byte-decidable signals approximate it; a function's tier is the worst it has (lower =
easier)::

    tier 0  no call, no outbound branch, no address-valued pool word  — a clean leaf
    tier 1  builds a PC-relative address (``add rd, pc, #imm``)       — a jump-table suspect
    tier 2  branches out, or a pool word is an address in the image    — relocated
    tier 3  body unreadable                                           — sorts last

* **branches out** — a ``BL``/``BLX`` (a call) *or* a ``B`` whose target lands outside the
  body (a **tail call**). Both leave the function and both force a call relocation. The
  "call-free" notion of v1 missed the tail-call half — the larger of the two in this image.
* **pool contents** — a PC-relative load (``ldr rd, [pc, #imm]``) reads a literal-pool word.
  Given the loaded-block map (:func:`load_blocks`), the word is **resolved** as a reference when
  *either* it is an absolute address inside the image, *or* it is a PC-relative offset that
  reaches the image (``pc + word``) — the PIC GOT idiom this image uses exclusively. Here *every*
  ``ldr rd, [pc, …]`` resolves to a reference, so a pool load is tier 2. A word resolving to
  neither (a genuine constant, e.g. a float) would leave the function clean — that case does not
  occur in this image. Without the map the contents cannot be resolved and any pool *use* is
  tier 1 (the conservative v2 behaviour).
* **PC-relative address** — ``add rd, pc, #imm`` (ADR) is self-relative and carries no
  relocation of its own, but frequently feeds a jump table whose *entries* are relocated; it
  stays in tier 1 as a suspect, since the table itself cannot be resolved from the body.
* ``size`` is the tiebreak within a tier (smaller first): the body length when read, else the
  inventory/partition length for an unreadable body.

All signals are **byte-pattern heuristics**: they scan 4-byte words for A32 encodings. A word of
literal-pool data that happens to match an encoding, or a constant that happens to equal a loaded
address, is a false positive — acceptable for a *ranking* prior (it never claims a match), and the
failure mode is to *demote* (the safe direction). Thumb is not handled — the target runs in ARM
state (``ARM:LE:32:v8``).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Image base of the loaded NSO (``docs/architecture.md`` → *Architecture*). ``.text`` starts
# here, so a ledger address maps to a plain byte offset from it.
BASE_ADDR = 0x60000000

# Difficulty for a body we could not read; it must never sort before a real function.
_UNREADABLE = 3


def is_call(word: int) -> bool:
    """Whether a 32-bit A32 word is a call: ``BL``, ``BLX`` (immediate), or ``BLX`` (register).

    ARM ``BL``        ``cccc 1011 iiii...``  (``cond`` anything but ``1111``)
    ARM ``BLX`` (imm) ``1111 101H iiii...``
    ARM ``BLX`` (reg) ``0001 0010 1111 1111 1111 0011 rrrr``
    """
    if word & 0xF0000000 == 0xF0000000:
        return (word & 0xFE000000) == 0xFA000000       # BLX (immediate)
    if word & 0x0F000000 == 0x0B000000:
        return True                                    # BL (cond != 1111)
    return (word & 0x0FFFFFF0) == 0x012FFF30           # BLX (register)


def has_call(body: bytes) -> bool:
    """Whether any 4-byte word in ``body`` decodes as a call (a heuristic; see the module doc)."""
    for off in range(0, len(body) - 3, 4):
        word = int.from_bytes(body[off:off + 4], "little")
        if is_call(word):
            return True
    return False


def branches_out(body: bytes) -> bool:
    """Whether the body calls (``BL``/``BLX``) or tail-calls (a ``B`` leaving the body).

    A ``B`` whose target lands outside ``[0, len(body))`` leaves the function; a target inside
    is an ordinary loop/branch. The target is computed PC-relative (``pc + 8 + imm24*4``), so
    the test needs no absolute address.
    """
    size = len(body)
    for off in range(0, size - 3, 4):
        word = int.from_bytes(body[off:off + 4], "little")
        if is_call(word):
            return True
        if word & 0xF0000000 == 0xF0000000:
            continue
        if word & 0x0F000000 == 0x0A000000:            # B (no link)
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            target = off + 8 + (imm << 2)
            if not (0 <= target < size):
                return True
    return False


def has_pool_load(body: bytes) -> bool:
    """Whether the body loads a literal pool word (A32 ``ldr rd, [pc, #±imm]``)."""
    for off in range(0, len(body) - 3, 4):
        word = int.from_bytes(body[off:off + 4], "little")
        if word & 0xF0000000 == 0xF0000000:
            continue
        if word & 0x0FFF0000 in (0x059F0000, 0x051F0000):
            return True
    return False


def has_adr(body: bytes) -> bool:
    """Whether the body builds a PC-relative address (A32 ``add rd, pc, #imm``).

    The address itself is self-relative (no relocation), but an ADR frequently feeds a jump
    table whose *entries* are relocated — so it stays a "suspect" signal when the table cannot
    be resolved.
    """
    for off in range(0, len(body) - 3, 4):
        word = int.from_bytes(body[off:off + 4], "little")
        if word & 0xF0000000 == 0xF0000000:
            continue
        if word & 0x0FFF0000 == 0x028F0000:
            return True
    return False


def has_literal_pool(body: bytes) -> bool:
    """Whether the body reads a PC-relative literal or builds a PC-relative address.

    Conservative: flags pool **use**, never the **contents** — the tier used when the loaded-block
    map is unavailable (see :func:`any_pool_pointer` for the resolved form).
    """
    return has_pool_load(body) or has_adr(body)


def any_pool_reference(body: bytes, addr: str, text: bytes, in_image) -> bool:
    """Whether a loaded pool word is a reference to the loaded image (a relocation site).

    Resolves every ``ldr rd, [pc, #±imm]`` in the body to its pool word and treats it as a
    reference when **either** form reaches the image: the word is an absolute address inside it,
    **or** it is a PC-relative offset (``pc + word`` lands inside it) — the PIC GOT idiom. A word
    that resolves to neither (a genuine constant, e.g. a float) leaves the function clean.

    In this image *every* pool word is the PC-relative form, so pool loads are always references;
    the absolute branch is kept so the test is correct on a non-PIC image too. Needs the absolute
    ``addr`` (to locate the pool and form ``pc``) and ``text`` (to read it).
    """
    base = int(addr, 16)
    for off in range(0, len(body) - 3, 4):
        word = int.from_bytes(body[off:off + 4], "little")
        if word & 0xF0000000 == 0xF0000000:
            continue
        if word & 0x0FFF0000 not in (0x059F0000, 0x051F0000):
            continue
        pc = base + off + 8
        imm = word & 0xFFF
        lit = pc + imm if (word & 0x00800000) else pc - imm
        lo = lit - BASE_ADDR
        if not 0 <= lo <= len(text) - 4:
            continue
        value = int.from_bytes(text[lo:lo + 4], "little")
        if in_image(value) or in_image((pc + value) & 0xFFFFFFFF):
            return True
    return False


def score(body: bytes | None, size: int, *, resolve=None) -> tuple[int, int]:
    """The easy-first key for one function; lower sorts first (see the tier table in the doc).

    ``body`` is the function's bytes (from :func:`body_of`) or ``None`` when they could not be
    read; ``size`` is its length from the inventory, used as the tiebreak for an unreadable body
    (when ``body`` is given the tiebreak is simply ``len(body)``).

    ``resolve`` is an optional ``body -> bool`` predicate (see :func:`any_pool_reference`, bound to
    one entry's address and image): when supplied, a body whose pool words are all constants is
    lifted to tier 0 and a body with a reference-valued pool word drops to tier 2. When absent,
    pool *use* is tier 1 (the conservative fallback).
    """
    if body is None:
        return (_UNREADABLE, size)
    if branches_out(body):
        return (2, len(body))
    if resolve is not None:
        if resolve(body):
            return (2, len(body))
        return (1, len(body)) if has_adr(body) else (0, len(body))
    if has_literal_pool(body):
        return (1, len(body))
    return (0, len(body))


def body_of(text: bytes, addr: str, size: int, base: int = BASE_ADDR) -> bytes | None:
    """Slice a function body out of a decompressed ``.text`` image, or ``None`` if out of range.

    ``addr`` is the ledger's 8-hex address; ``size`` is the body length.
    """
    try:
        off = int(addr, 16) - base
    except ValueError:
        return None
    if off < 0 or size <= 0 or off + size > len(text):
        return None
    return text[off:off + size]


def _in_image(ranges: list[tuple[int, int]]) -> Callable[[int], bool]:
    """A ``value -> bool`` predicate: is ``value`` inside any loaded-block range?"""
    def pred(value: int) -> bool:
        return any(lo <= value < hi for lo, hi in ranges)
    return pred


def make_key(text: bytes, sizes: dict[str, int],
             blocks: list[tuple[int, int]] | None = None) -> Callable[[dict], tuple[int, int]]:
    """Build the selector key for ``select(..., key=...)`` from a ``.text`` image and body sizes.

    ``sizes`` maps ``addr -> body size`` (``bundle.parse_inventory``). An entry absent from
    ``sizes`` falls back to the ledger partition ``size``, and if its body cannot be sliced the
    key degrades to the unreadable bucket — the entry still sorts, it just sorts last.

    ``blocks`` is the loaded-image block map as ``(start, end)`` address ranges
    (:func:`load_blocks`). When given, pool **contents** are resolved, so a constant-pool leaf
    stays in tier 0 (:func:`any_pool_pointer`). When ``None`` the tiering is conservative — any
    pool *use* is tier 1.
    """
    in_image = _in_image(blocks) if blocks else None

    def key(entry: dict) -> tuple[int, int]:
        addr = entry["addr"]
        try:
            size = sizes[addr]
        except KeyError:
            size = int(entry.get("size") or 0)
        body = body_of(text, addr, size)
        if in_image is None:
            return score(body, size)
        return score(body, size,
                     resolve=lambda b: any_pool_reference(b, addr, text, in_image))
    return key


def load_blocks(path) -> list[tuple[int, int]]:
    """Parse an ``inventory.blocks.tsv`` into ``(start, end)`` address ranges; ``[]`` if absent.

    Columns are ``block, class, addr, size`` (``addr``/``size`` hex). The ranges feed
    :func:`any_pool_pointer` as the loaded-image map. A missing or malformed file yields ``[]``,
    which drops the key back to the conservative pool-use tier — never an error.
    """
    try:
        lines = Path(path).read_text().splitlines()
    except OSError:
        return []
    ranges: list[tuple[int, int]] = []
    for line in lines:
        fields = line.split("\t")
        if len(fields) < 4 or fields[0] == "block":
            continue
        try:
            start, size = int(fields[2], 16), int(fields[3], 16)
        except ValueError:
            continue
        if size > 0:
            ranges.append((start, start + size))
    return ranges


def load_text(nso) -> bytes | None:
    """The decompressed reference ``.text`` for ``nso``, or ``None`` if it cannot be read.

    The **one** impure convenience in this module: every :func:`score`/:func:`make_key` call is
    pure, but this reads the NSO (pure-Python LZ4 via ``tools/nso/nso_extract.py``, no Ghidra)
    so callers — the loop and the manual tooling alike — do not each repeat the same three lines.
    It never raises: a missing or malformed image yields ``None``, and an ordering that uses it
    simply degrades to address order. These are exactly the bytes the gate compares against:
    the image's ``.text`` carries no relocations of its own (they all land in ``.data``/``.got``).
    """
    try:
        sys.path.insert(0, str(REPO / "tools" / "nso"))
        import nso_extract
    except ImportError:
        return None
    try:
        return nso_extract.extract(Path(nso))["data"]["text"]
    except (nso_extract.NsoError, OSError, KeyError):
        return None
