"""Advisory lint for mis-segmented ledger entries (fragments of a larger function).

The committed ledger is seeded from the Ghidra inventory export, whose function list is a
*draft*. In code with many indirect branches, function pointers, and jump tables, Ghidra
sometimes promotes an address **inside** a real function to a ``function`` entry, and its
hole-y function bodies leave interior bytes to be materialised as ``D_<addr>`` gap blobs. A
fragment like that reads registers set by the preceding instructions, so it can never be
reconstructed standalone — it just wastes the reconstruction loop (see ``AGENTS.md`` →
*Validation*, and ``tools/ledger/reconcile.py`` for the fix).

This tool **flags** such entries; it never edits the ledger (that is ``reconcile.py``'s job,
behind a human-reviewed override). It is a heuristic, so its output is a *review queue*, not
a verdict — a real leaf function that reaches the next entry through a tail call or a
pointer could be flagged, which is why ``--around`` prints the surrounding boundaries and
the underlying evidence rather than a bare list.

Signals (all byte-pattern; ARM state only — the target is ``ARM:LE:32:v8``):

* **no-exit** — a function must leave itself, so a body with no return (``pop {…, pc}``/``ldm … pc``,
  ``bx``/``blx``, ``mov pc, …``, a data-processing op with ``Rd == pc``, or ``ldr pc, […]``),
  no tail call (an unconditional ``b`` to a target outside the body — the
  ``pop {…, lr}; b <callee>`` sibling-call epilogue), and no noreturn tail (an unconditional
  ``bl`` as the last code instruction, i.e. a call to a function that never returns) cannot be
  a whole function. **Strong** (a fragment).
* **no-entry-signal** — the entry address is neither a prologue (``push``/``stmdb sp!``) nor
  a ``BL`` target anywhere in ``.text``. Every real non-leaf function is one or the other,
  so this is a **suspect** signal (a leaf function reached only by tail call or pointer would
  trip it).

Reads the reference ``.text`` through ``complexity.load_text`` (pure Python, no Ghidra).

Usage::

    python3 tools/ledger/fragments.py                          # full ledger, summary
    python3 tools/ledger/fragments.py --list                   # every flagged entry
    python3 tools/ledger/fragments.py --around 60c4a194 --span 0x900   # trace one region
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from complexity import BASE_ADDR, body_of, load_text
from ledgerlib import read_entries

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_NSO = REPO / "baserom" / "main.nso"


# --- A32 primitives (byte patterns; PC-writing and prologue) --------------------------

def is_prologue(word: int) -> bool:
    """``stmdb sp!, {…}`` (the ``push`` alias) — the common A32 non-leaf prologue."""
    return (word & 0xFFFF0000) == 0xE92D0000


def writes_pc(word: int) -> bool:
    """Whether an A32 word writes the PC as a control transfer (a return / tail branch)."""
    if word >> 28 == 0xF:                       # cond == 1111 is never an ARM instruction
        return False
    if (word & 0x0FFFFFF0) in (0x012FFF10, 0x012FFF30):     # bx rN / blx rN
        return True
    if (word & 0x0E000000) == 0x08000000 and (word & 0x00100000) and (word & 0x8000):
        return True                             # ldm/ldmia ..., {…, pc}
    if (word & 0x0C100000) == 0x04100000 and (word & 0xF000) == 0xF000:
        return True                             # ldr pc, […]  (jump-table / epilogue)
    if (word & 0x0C000000) == 0x00000000 and (word & 0xF000) == 0xF000:
        op = (word >> 21) & 0xF                   # data-processing with Rd == pc
        if op not in (0b1000, 0b1001, 0b1010):   # exclude TST/TEQ/CMP (S-only)
            return True
    return False


def pool_offsets(body: bytes) -> set[int]:
    """Body-relative offsets of literal-pool words: the targets of ``ldr rd, [pc, #±imm]`` and
    ``add rd, pc, #imm``. Words here are data, not instructions, so the exit scan skips them."""
    size = len(body)
    out: set[int] = set()
    for o in range(0, size - 3, 4):
        w = int.from_bytes(body[o:o + 4], "little")
        if w >> 28 == 0xF:
            continue
        pc = o + 8
        if (w & 0x0FFF0000) in (0x059F0000, 0x051F0000):         # ldr rd, [pc, #±imm]
            imm = w & 0xFFF
            lit = pc + imm if (w & 0x00800000) else pc - imm
        elif (w & 0x0FFF0000) == 0x028F0000:                     # add rd, pc, #imm
            lit = pc + (w & 0xFFF)
        else:
            continue
        if 0 <= lit <= size - 4:
            out.add(lit)
    return out


def has_exit(body: bytes) -> bool:
    """Whether the body can leave the function: a return, a tail call, or a noreturn tail.

    A return is any instruction that writes the PC (:func:`writes_pc`). A tail call is an
    unconditional branch to a target **outside** the body — the ``pop {…, lr}; b <callee>``
    epilogue the compiler emits for a sibling call (a branch *inside* the body is a loop). A
    **noreturn tail** is an unconditional ``bl``/``blx`` as the last *code* instruction (the
    callee never returns, so the compiler emits no epilogue); literal-pool words are skipped
    so a trailing pool does not hide it.
    """
    size = len(body)
    pool = pool_offsets(body)
    code = [o for o in range(0, size - 3, 4) if o not in pool]
    for o in code:
        w = int.from_bytes(body[o:o + 4], "little")
        if writes_pc(w):
            return True
        if (w >> 28) == 0xE and ((w >> 24) & 0xF) == 0xA:        # B (tail call if it leaves)
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            target = o + 8 + (imm << 2)
            if not 0 <= target < size:
                return True
    if code:
        last = int.from_bytes(body[code[-1]:code[-1] + 4], "little")
        if (last >> 28) == 0xE and ((last >> 24) & 0xF) == 0xB:  # ends on a non-returning call
            return True
    return False


def first_word(body: bytes) -> int | None:
    return int.from_bytes(body[:4], "little") if len(body) >= 4 else None


def branch_targets(text: bytes) -> tuple[set[int], set[int]]:
    """``(bl_targets, b_targets)`` — absolute addresses called / branched to in ``text``."""
    bl: set[int] = set()
    b: set[int] = set()
    for i in range(len(text) // 4):
        w = int.from_bytes(text[i * 4:i * 4 + 4], "little")
        if w >> 28 == 0xF:
            continue
        op = (w >> 24) & 0xF
        if op not in (0xA, 0xB):
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        target = (BASE_ADDR + i * 4 + 8 + (imm << 2)) & 0xFFFFFFFF
        (bl if op == 0xB else b).add(target)
    return bl, b


# --- classification -------------------------------------------------------------------

class Finding:
    def __init__(self, entry: dict, reasons: list[str], prologue: bool, bl_target: bool,
                 terminated: bool):
        self.entry = entry
        self.reasons = reasons
        self.prologue = prologue
        self.bl_target = bl_target
        self.terminated = terminated


def classify(entries: list[dict], text: bytes, bl_targets: set[int]) -> list[Finding]:
    """Return a finding for every ``function`` entry that looks like a fragment."""
    findings: list[Finding] = []
    for e in entries:
        if e["kind"] != "function" or e["block"] != ".text":
            continue
        addr = int(e["addr"], 16)
        body = body_of(text, e["addr"], int(e["size"]))
        if body is None or len(body) < 4:
            continue                                   # unreadable — not this lint's concern
        terminated = has_exit(body)
        fw = first_word(body)
        prologue = fw is not None and is_prologue(fw)
        is_bl = addr in bl_targets
        reasons: list[str] = []
        if not terminated:
            reasons.append("no-exit")
        if not prologue and not is_bl:
            reasons.append("no-entry-signal")
        if reasons:
            findings.append(Finding(e, reasons, prologue, is_bl, terminated))
    return findings


# --- CLI ------------------------------------------------------------------------------

def _print_trace(entries: list[dict], text: bytes, bl: set[int], b: set[int], around: int,
                 span: int) -> None:
    lo, hi = around - span, around + span
    print(f"region {lo:08x}..{hi:08x}")
    for e in entries:
        if e["kind"] == "external" or e["block"] != ".text":
            continue
        a = int(e["addr"], 16)
        if not lo <= a < hi:
            continue
        body = body_of(text, e["addr"], int(e["size"]))
        fw = first_word(body) if body else None
        flags = []
        if body is None:
            flags.append("unreadable")
        else:
            flags.append("prologue" if (fw is not None and is_prologue(fw)) else "-")
            flags.append("term" if has_exit(body) else "NO-TERM")
        flags.append("bl" if a in bl else "-")
        flags.append("b" if a in b else "-")
        mark = " <== suspect" if (body is not None and
                                  (not has_exit(body))) else ""
        print(f"  {e['addr']}  {e['kind']:8s} size={int(e['size']):5d}  "
              f"{' '.join(flags):20s} {e['name']}{mark}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO)
    ap.add_argument("--list", action="store_true", help="print every flagged entry")
    ap.add_argument("--around", default=None, help="trace one address (hex)")
    ap.add_argument("--span", type=lambda s: int(s, 16), default=0x400,
                    help="half-window for --around (hex, default 0x400)")
    args = ap.parse_args(argv)

    text = load_text(args.nso)
    if text is None:
        print(f"error: cannot read {args.nso}", file=sys.stderr)
        return 2
    entries = read_entries(args.ledger)
    bl, b = branch_targets(text)

    if args.around:
        _print_trace(entries, text, bl, b, int(args.around, 16), args.span)
        return 0

    findings = classify(entries, text, bl)
    strong = [f for f in findings if "no-exit" in f.reasons]
    suspect = [f for f in findings if f.reasons == ["no-entry-signal"]]
    print(f"fragments: {len(findings)} flagged of "
          f"{sum(1 for e in entries if e['kind'] == 'function')} functions")
    print(f"  no-exit         {len(strong)}   (a function must return, tail-call, or not return)")
    print(f"  no-entry-signal {len(suspect)}   (no prologue and not a BL target)")
    if args.list:
        for f in findings:
            print(f"  {f.entry['addr']}  size={int(f.entry['size']):5d}  "
                  f"{','.join(f.reasons):30s}  {f.entry['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
