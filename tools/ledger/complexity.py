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

The metric (v1)
---------------
The gate can currently verify a **relocation-free leaf** cleanly; a function whose object
carries relocations needs the not-yet-built relocation-aware diff
(``tools/ledger/bytegate.py`` → *Scope*). Because this image's relocations all land in
``.data``/``.got`` (its ``.text`` carries none), "relocation-free" cannot be read off the
image's relocation tables — it is a property of what the *reconstruction* will need, and the
strong, cheap proxy for it is **call-free**: a function that makes no ``BL``/``BLX`` gives
clang no call relocation and is almost always a self-contained leaf. So the key is, lower =
easier::

    (has_call, size)

* ``has_call`` — 0 if the body contains no call instruction, else 1. Call-free first.
* ``size``     — the function's body length; smaller first.

A body that could not be read (its block was not available) sorts **last** with key
``(2, size)``, so unknown entries never jump the queue.

Call detection is a **byte-pattern heuristic**: it scans 4-byte words for the A32 ``BL`` and
``BLX`` encodings. A word of literal-pool data that happens to match one of those patterns
would be a false positive. This is acceptable for a *ranking* prior (it never claims a
match), and refines later with literal-pool and global-reference detection. Thumb is not
handled — the target runs in ARM state (``ARM:LE:32:v8``).
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
_UNREADABLE = 2


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


def score(body: bytes | None, size: int) -> tuple[int, int]:
    """The easy-first key for one function; lower sorts first.

    ``body`` is the function's bytes (from :func:`body_of`) or ``None`` when they could not be
    read; ``size`` is its length from the inventory (used only for the unreadable fallback, and
    as the length when ``body`` is given it is simply ``len(body)``).
    """
    if body is None:
        return (_UNREADABLE, size)
    return (1 if has_call(body) else 0, len(body))


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


def make_key(text: bytes, sizes: dict[str, int]) -> Callable[[dict], tuple[int, int]]:
    """Build the selector key for ``select(..., key=...)`` from a ``.text`` image and body sizes.

    ``sizes`` maps ``addr -> body size`` (``bundle.parse_inventory``). An entry absent from
    ``sizes`` falls back to the ledger partition ``size``, and if its body cannot be sliced the
    key degrades to the unreadable bucket — the entry still sorts, it just sorts last.
    """
    def key(entry: dict) -> tuple[int, int]:
        addr = entry["addr"]
        try:
            size = sizes[addr]
        except KeyError:
            size = int(entry.get("size") or 0)
        return score(body_of(text, addr, size), size)
    return key


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
