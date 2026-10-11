"""Normalized A32 shape signatures + a corpus histogram — the "what shapes recur?" lens.

Templates (`tools/ledger/templates.py`) cover a handful of shapes we already trusted; this
module answers the *next* question, empirically: across the pending corpus, which instruction
shapes actually recur, and often enough to be worth a rule? It exists so template growth is
**data-driven** rather than guessed (the lesson from sm64ds: its mwccarm/ARM9 shape list does
not port wholesale).

It is a **library**, not a CLI (the same placement rule as `complexity.py` and `templates.py`:
ledger-derived analysis the reconstruction loop and future manual tooling both call). The core
is pure — `bytes -> tuple[str, ...]` and a histogram over those — so it is trivially
unit-testable and safe to call from anywhere.

Two things here are deliberately coarse and **honest** about it:

* :func:`decode` is a *shape* decoder, not a full disassembler. It recognizes the common A32
  encodings (data-processing, load/store single/multiple/halfword, branch, multiply, the
  bx/blx/clz misc group, movw/movt, VFP/NEON) and, for anything it does not model, emits a
  category token derived from the encoding class (e.g. ``"mediaeq"``). Registers and conditions
  are kept; immediates and offsets are collapsed to ``#`` so two spellings of "the same shape"
  cluster together. It never claims a match — a signature is a clustering key, nothing more.
* :func:`histogram` counts exact signatures. That is the right granularity for *deciding what to
  template*, but it is not a claim that a signature is templatable; the gate still disposes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence

# Condition suffixes indexed by the 4-bit cond field (one canonical spelling each: CS==HS,
# CC==LO); index 14 (AL) is emitted as "", index 15 is the never/undefined condition.
_COND = ("eq", "ne", "cs", "cc", "mi", "pl", "vs", "vc",
         "hi", "ls", "ge", "lt", "gt", "le", "", "nv")

# Data-processing opcodes (bits 24:21); immediate and register forms share the table.
_DP = ("and", "eor", "sub", "rsb", "add", "adc", "sbc", "rsc",
       "tst", "teq", "cmp", "cmn", "orr", "mov", "bic", "mvn")
_DP_CMP = (8, 9, 10, 11)                          # tst/teq/cmp/cmn: no Rd, flags implied
_SHIFT = ("lsl", "lsr", "asr", "ror")


def _reg(n: int) -> str:
    """Render a register number as its A32 name (``r0``-``r15``)."""
    return ("r" + str(n)) if n < 13 else ("sp" if n == 13 else "lr" if n == 14 else "pc")


def _cond(w: int) -> tuple[str, int]:
    """``(condition-suffix, cond-field)``; the suffix is ``""`` for AL."""
    c = (w >> 28) & 0xF
    return (_COND[c], c)


def _reglist(mask: int) -> str:
    """A register-list operand, e.g. ``{r4,r5,lr}``."""
    return "{" + ",".join(_reg(i) for i in range(16) if mask & (1 << i)) + "}"


def _shifted_reg(w: int) -> str:
    """Operand-2 for a register form: ``rX``, ``rX,lsl #``, or ``rX,lsl rY`` (register shift)."""
    rm = _reg(w & 0xF)
    if (w >> 4) & 1:                                  # register-shifted register
        return f"{rm},{_SHIFT[(w >> 5) & 3]} {_reg((w >> 8) & 0xF)}"
    amount = (w >> 7) & 0x1F
    if amount == 0 and ((w >> 5) & 3) == 0:           # no shift: LSL #0 is a plain move
        return rm
    return f"{rm},{_SHIFT[(w >> 5) & 3]} #"


def _dp(w: int, cond: str) -> str:
    """Data-processing (``top`` 000 register / 001 immediate)."""
    imm = (w >> 25) & 1
    op = (w >> 21) & 0xF
    mnem = _DP[op]
    if (w >> 20) & 1 and op not in _DP_CMP:           # 's' flag, but comparisons imply it
        mnem += "s"
    rn = _reg((w >> 16) & 0xF)
    rd = _reg((w >> 12) & 0xF)
    op2 = "#" if imm else _shifted_reg(w)
    if op in (13, 15):                                # mov / mvn: no Rn
        return f"{mnem}{cond} {rd},{op2}"
    if op in _DP_CMP:                                 # tst/teq/cmp/cmn: no Rd
        return f"{mnem}{cond} {rn},{op2}"
    return f"{mnem}{cond} {rd},{rn},{op2}"


def _mul(w: int, cond: str) -> str:
    """The multiply family (``bits 27:23 == 00000``, ``bits 7:4 == 1001``)."""
    op = (w >> 21) & 0x7
    rd = _reg((w >> 16) & 0xF)
    rn = _reg((w >> 12) & 0xF)
    rs = _reg((w >> 8) & 0xF)
    rm = _reg(w & 0xF)
    if op == 0:
        return f"mul{cond} {rd},{rm},{rs}"
    if op == 1:
        return f"mla{cond} {rd},{rm},{rs},{rn}"
    if op in (4, 6):                                  # long multiply: 4=U=0, 6=U=1 (bit22)
        # Encoding holds RdHi at bits[19:16] and RdLo at bits[15:12]; the syntax is
        # `umull RdLo, RdHi, Rm, Rs`, so rn (RdLo) prints before rd (RdHi).
        mnem = {4: "umull", 6: "smull"}[op] + ("al" if (w >> 20) & 1 else "")
        return f"{mnem}{cond} {rn},{rd},{rm},{rs}"
    return f"mulx{cond} {rd},{rn},{rm},{rs}"


def _misc(w: int, cond: str) -> str:
    """The misc/bx group (``bits 27:23 == 00010``, ``bits 7:4 == 1001``)."""
    if (w & 0x0FFFFFF0) == 0x012FFF10:
        return f"bx{cond} {_reg(w & 0xF)}"
    if (w & 0x0FFFFFF0) == 0x012FFF30:
        return f"blx{cond} {_reg(w & 0xF)}"
    if (w & 0x0FFF0FF0) == 0x016F0F10:
        return f"clz{cond} {_reg((w >> 12) & 0xF)},{_reg(w & 0xF)}"
    if (w & 0x0FF000F0) == 0x01200070:
        return "bkpt #"
    if (w & 0x0FB00FF0) == 0x01000090:                # swp / swpb
        b = "b" if (w >> 22) & 1 else ""
        return (f"swp{b}{cond} {_reg((w >> 12) & 0xF)},"
                f"{_reg(w & 0xF)},[{_reg((w >> 16) & 0xF)}]")
    return f"misc{cond} #"


def _ldst(w: int, cond: str) -> str:
    """Single data transfer, word/byte (``top`` 010 immediate / 011 register offset)."""
    i = (w >> 25) & 1
    p = (w >> 24) & 1
    b = "b" if (w >> 22) & 1 else ""
    wr = (w >> 21) & 1
    l = "ldr" if (w >> 20) & 1 else "str"
    rn = _reg((w >> 16) & 0xF)
    rd = _reg((w >> 12) & 0xF)
    off = _shifted_reg(w) if i else "#"
    if p:
        mem = f"[{rn},{off}]" + ("!" if wr else "")
    else:
        mem = f"[{rn}],{off}"
        if not wr:                                    # P=0, W=0 -> unprivileged (T) form
            l += "t"
    return f"{l}{b}{cond} {rd},{mem}"


def _ldst_half(w: int, cond: str) -> str:
    """Halfword / signed transfer (``top`` 000, ``bits 7:4`` in 1011/1101/1111)."""
    p = (w >> 24) & 1
    i = (w >> 22) & 1                              # NB: 1 = immediate here (opposite of single)
    wr = (w >> 21) & 1
    l = (w >> 20) & 1
    op = (w >> 5) & 0x3
    rn = _reg((w >> 16) & 0xF)
    rd = _reg((w >> 12) & 0xF)
    mnem = {1: "ldrh" if l else "strh", 2: "ldrsb", 3: "ldrsh"}.get(
        op, "ldrhx" if l else "strhx")
    off = "#" if i else _reg(w & 0xF)
    mem = (f"[{rn},{off}]" + ("!" if wr else "")) if p else f"[{rn}],{off}"
    return f"{mnem}{cond} {rd},{mem}"


def _ldm_stm(w: int, cond: str) -> str:
    """Load/store multiple (``top`` 100), with the push/pop special cases."""
    p = (w >> 24) & 1
    u = (w >> 23) & 1
    s = "^" if (w >> 22) & 1 else ""
    wr = (w >> 21) & 1
    l = (w >> 20) & 1
    rn = _reg((w >> 16) & 0xF)
    regs = _reglist(w & 0xFFFF)
    if rn == "sp":
        if p and not u and wr and not l:
            return f"push{cond} {regs}{s}"
        if not p and u and wr and l:
            return f"pop{cond} {regs}{s}"
    mode = {(0, 0): "da", (0, 1): "ia", (1, 0): "db", (1, 1): "ib"}[(p, u)]
    return f"{'ldm' if l else 'stm'}{mode}{cond} {rn}{'!' if wr else ''},{regs}{s}"


def _branch(w: int, cond: str, cfield: int) -> str:
    """Branches (``top`` 101), including the BLX-immediate special case (cond == 1111)."""
    if cfield == 0xF:
        return "blx #"
    return f"{'bl' if (w >> 24) & 1 else 'b'}{cond} #"


def _coproc_class(w: int) -> str:
    """A coarse class for the coprocessor / VFP / NEON / unconditional space."""
    cp = (w >> 8) & 0xF
    if ((w >> 25) & 7) == 6:
        return "vfp.d" if cp == 11 else "vfp.s" if cp == 10 else "coproc"
    return "neon" if ((w >> 24) & 1) == 0 else "undecoded.uncond"


def decode(word: int) -> str:
    """One A32 word to a normalized shape token (registers/condition kept, immediates ``#``).

    Undecoded words yield a category token rather than raising — a corpus histogram must never
    be sunk by one odd encoding.
    """
    cond, cfield = _cond(word)
    top = (word >> 25) & 7
    if top == 0:
        # The misc group (bx/blx/clz/mrs/msr/swp/bkpt) occupies bits[27:20] in
        # {0x10,0x12,0x14,0x16} -- the S=0 spellings of opcodes 1000..1011, which are
        # undefined for the comparisons, so this routing never steals a real data-proc op.
        if ((word >> 20) & 0xFF) in (0x10, 0x12, 0x14, 0x16):
            return _misc(word, cond)
        nib = (word >> 4) & 0xF
        if nib == 0x9:                                # multiply / media (bits 7:4 == 1001)
            if (word >> 23) & 0x1F in (0x00, 0x01):   # mul/mla (00000) and long multiply (00001)
                return _mul(word, cond)
            return f"media{cond}"
        if ((word >> 7) & 1) and (nib & 1):           # halfword/signed (bits 7:4 in B/D/F)
            return _ldst_half(word, cond)
        return _dp(word, cond)
    if top == 1:
        if (word & 0x0FF00000) == 0x03000000:
            return f"movw{cond} {_reg((word >> 12) & 0xF)},#"
        if (word & 0x0FF00000) == 0x03400000:
            return f"movt{cond} {_reg((word >> 12) & 0xF)},#"
        return _dp(word, cond)
    if top in (2, 3):
        return _ldst(word, cond)
    if top == 4:
        return _ldm_stm(word, cond)
    if top == 5:
        return _branch(word, cond, cfield)
    return f"{_coproc_class(word)}{cond}"


def signature(body: bytes) -> tuple[str, ...]:
    """The normalized shape signature of a function body: one token per whole A32 word.

    A trailing partial word (a body not a multiple of 4) is ignored — it cannot be an
    instruction, and including it would only split otherwise-identical clusters.
    """
    return tuple(decode(int.from_bytes(body[i:i + 4], "little"))
                 for i in range(0, len(body) - 3, 4))


def render_sig(sig: Sequence[str]) -> str:
    """A signature as a single ``;``-joined line, for reports and golden tests."""
    return "; ".join(sig)


def histogram(sigs: Iterable[Sequence[str]]) -> Counter:
    """Count exact signatures; the ticket for deciding what is worth templating."""
    return Counter(tuple(s) for s in sigs)
