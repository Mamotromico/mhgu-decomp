"""Deterministic templates for trivial leaf shapes — propose; the gate disposes.

Some functions have exactly one plausible C spelling. An empty body is ``void f() {}``; a
constant return is ``int f() { return K; }``; and so on. For these, an LLM adds nothing but
latency and variance — a small rule that recognizes the *bytes* and emits the canonical source
reproduces them deterministically and for free.

This module is that rulebook. It is a **library**, not a CLI: the reconstruction loop
(``tools/loop/run.py``) consults it before calling the model, and manual-decomp tooling can call
it the same way (``propose`` — "what would the template emit for this function?"). It is pure:
``bytes -> str | None``, no filesystem, no ledger, no network.

**It never claims a match.** A template only *proposes* a candidate; the byte gate
(``tools/ledger/bytegate.py``) still compiles it and compares, and only a gate ``match`` counts.
So a wrong template is a near miss, never a false match, and the loop falls through to the model
on a gate miss — a bad template costs at most one wasted gate run, never a wasted model call.

Coverage is deliberately narrow and extensible: each :class:`Template` is one exact instruction
pattern paired with the C++ that reproduces it. Adding a shape is adding one entry.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

# A32 encodings we recognize (condition AL; the target runs in ARM state, ARM:LE:32:v8).
_W_BX_LR = 0xE12FFF1E          # bx lr
_ALU_OP_MASK = 0xFFFFF000      # cond + opcode (immediate, no S) + rd=r0


def _words(body: bytes) -> list[int]:
    """The body's 32-bit little-endian words (A32 is fixed-width)."""
    return [int.from_bytes(body[i:i + 4], "little") for i in range(0, len(body) - 3, 4)]


def _ror(value: int, amount: int) -> int:
    """32-bit rotate-right; A32 immediate operands are an 8-bit value rotated by an even amount."""
    amount &= 31
    return ((value >> amount) | (value << (32 - amount))) & 0xFFFFFFFF


def _imm12(w: int) -> int:
    """The 32-bit constant of a data-processing immediate instruction (imm8 rotated)."""
    return _ror(w & 0xFF, ((w >> 8) & 0xF) * 2)


def _movw_imm(w: int) -> int:
    """The 16-bit immediate of ``movw rd, #imm16`` (imm4:imm12, low to high)."""
    return (((w >> 16) & 0xF) << 12) | (w & 0xFFF)


def _half_off(w: int) -> int:
    """The byte displacement of a halfword/signed access (imm4H:imm4L). U=1 enforced by callers."""
    return ((w >> 4) & 0xF0) | (w & 0xF)


def _signed(v: int) -> int:
    """Interpret a 32-bit value as a C ``int`` (so it renders as an ``int`` literal)."""
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


# --- the symbol binding: identical rule to the loop's ``run.build_prompt`` ------------------

def _decl(symbol: str) -> tuple[str, str]:
    """``(cxx_name, trailing_asm)`` so the object symbol is exactly ``symbol``.

    A valid identifier is used verbatim; otherwise a C++-legal name is bound to the exact
    symbol with a trailing ``asm`` on the declaration (the definition then follows).
    """
    if symbol.isidentifier():
        return symbol, ""
    return "reconstructed", f' asm("{symbol}")'


def _render_void(symbol: str) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" void {cxx}(void){binding};\n'
            f'extern "C" void {cxx}(void) {{}}\n')


def _render_int(symbol: str, value: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" int {cxx}(void){binding};\n'
            f'extern "C" int {cxx}(void) {{ return {value}; }}\n')


def _is_mov_r0_imm(w: int) -> bool:
    return (w & _ALU_OP_MASK) == 0xE3A00000       # mov r0, #imm


def _is_mvn_r0_imm(w: int) -> bool:
    return (w & _ALU_OP_MASK) == 0xE3E00000       # mvn r0, #imm


def _is_ldr_r0(w: int) -> bool:
    return (w & 0x0FFF0000) == 0x05900000        # ldr r0, [r0, #imm]   (U=1)


def _is_ldrb_r0(w: int) -> bool:
    return (w & 0x0FFF0000) == 0x05D00000        # ldrb r0, [r0, #imm]


def _is_str_r1(w: int) -> bool:
    return (w & 0x0FFFF000) == 0x05801000        # str r1, [r0, #imm]


def _is_strb_r1(w: int) -> bool:
    return (w & 0x0FFFF000) == 0x05C01000        # strb r1, [r0, #imm]


def _is_mov_r1_imm(w: int) -> bool:
    return (w & 0xFFFFF000) == 0xE3A01000        # mov r1, #imm


def _is_add_r0_imm(w: int) -> bool:
    return (w & 0xFFFFF000) == 0xE2800000        # add r0, r0, #imm


def _is_ldrh_r0(w: int) -> bool:
    return (w & 0xFFFFF0F0) == 0xE1D000B0        # ldrh r0, [r0, #imm]  (U=1)


def _is_ldrsb_r0(w: int) -> bool:
    return (w & 0xFFFFF0F0) == 0xE1D000D0        # ldrsb r0, [r0, #imm]  (U=1)


def _is_movw_r1(w: int) -> bool:
    return (w & 0xFFF0F000) == 0xE3001000        # movw r1, #imm16


def _is_ldr_r0_r1(w: int) -> bool:
    return (w & 0x0FFFFFFF) == 0x07900001        # ldr r0, [r0, r1]


def _is_ldrb_r0_r1(w: int) -> bool:
    return (w & 0x0FFFFFFF) == 0x07D00001        # ldrb r0, [r0, r1]


def _render_get_word(symbol: str, offset: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" int {cxx}(char *p){binding};\n'
            f'extern "C" int {cxx}(char *p) {{ return *(int *)(p + {offset}); }}\n')


def _render_get_byte(symbol: str, offset: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" int {cxx}(unsigned char *p){binding};\n'
            f'extern "C" int {cxx}(unsigned char *p) {{ return p[{offset}]; }}\n')


def _render_set_word(symbol: str, offset: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" void {cxx}(char *p, int v){binding};\n'
            f'extern "C" void {cxx}(char *p, int v) {{ *(int *)(p + {offset}) = v; }}\n')


def _render_set_byte(symbol: str, offset: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" void {cxx}(unsigned char *p, unsigned char v){binding};\n'
            f'extern "C" void {cxx}(unsigned char *p, unsigned char v) {{ p[{offset}] = v; }}\n')


def _render_add_const(symbol: str, k: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" int {cxx}(int x){binding};\n'
            f'extern "C" int {cxx}(int x) {{ return x + {k}; }}\n')


def _render_store_word(symbol: str, offset: int, k: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" void {cxx}(char *p){binding};\n'
            f'extern "C" void {cxx}(char *p) {{ *(int *)(p + {offset}) = {k}; }}\n')


def _render_store_byte(symbol: str, offset: int, k: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" void {cxx}(unsigned char *p){binding};\n'
            f'extern "C" void {cxx}(unsigned char *p) {{ p[{offset}] = {k}; }}\n')


def _render_get_half(symbol: str, offset: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" int {cxx}(char *p){binding};\n'
            f'extern "C" int {cxx}(char *p) {{ return *(unsigned short *)(p + {offset}); }}\n')


def _render_get_sbyte(symbol: str, offset: int) -> str:
    cxx, binding = _decl(symbol)
    return (f'extern "C" int {cxx}(char *p){binding};\n'
            f'extern "C" int {cxx}(char *p) {{ return *(signed char *)(p + {offset}); }}\n')


@dataclass(frozen=True)
class Template:
    """One recognized shape: an instruction-pattern predicate and the C++ that reproduces it."""

    name: str
    match: Callable[[list[int]], bool]
    render: Callable[[str, list[int]], str]


TEMPLATES: tuple[Template, ...] = (
    Template(
        "void-return",
        lambda ws: len(ws) == 1 and ws[0] == _W_BX_LR,
        lambda sym, ws: _render_void(sym),
    ),
    Template(
        "return-const",
        lambda ws: len(ws) == 2 and ws[1] == _W_BX_LR and _is_mov_r0_imm(ws[0]),
        lambda sym, ws: _render_int(sym, _signed(_imm12(ws[0]))),
    ),
    Template(
        "return-not-const",
        lambda ws: len(ws) == 2 and ws[1] == _W_BX_LR and _is_mvn_r0_imm(ws[0]),
        lambda sym, ws: _render_int(sym, _signed(~_imm12(ws[0]))),
    ),
    Template(
        "word-getter",
        lambda ws: len(ws) == 2 and ws[1] == _W_BX_LR and _is_ldr_r0(ws[0]),
        lambda sym, ws: _render_get_word(sym, ws[0] & 0xFFF),
    ),
    Template(
        "byte-getter",
        lambda ws: len(ws) == 2 and ws[1] == _W_BX_LR and _is_ldrb_r0(ws[0]),
        lambda sym, ws: _render_get_byte(sym, ws[0] & 0xFFF),
    ),
    Template(
        "word-setter",
        lambda ws: len(ws) == 2 and ws[1] == _W_BX_LR and _is_str_r1(ws[0]),
        lambda sym, ws: _render_set_word(sym, ws[0] & 0xFFF),
    ),
    Template(
        "byte-setter",
        lambda ws: len(ws) == 2 and ws[1] == _W_BX_LR and _is_strb_r1(ws[0]),
        lambda sym, ws: _render_set_byte(sym, ws[0] & 0xFFF),
    ),
    Template(
        "add-const",
        lambda ws: len(ws) == 2 and ws[1] == _W_BX_LR and _is_add_r0_imm(ws[0]),
        lambda sym, ws: _render_add_const(sym, _imm12(ws[0])),
    ),
    Template(
        "half-getter",
        lambda ws: len(ws) == 2 and ws[1] == _W_BX_LR and _is_ldrh_r0(ws[0]),
        lambda sym, ws: _render_get_half(sym, _half_off(ws[0])),
    ),
    Template(
        "sbyte-getter",
        lambda ws: len(ws) == 2 and ws[1] == _W_BX_LR and _is_ldrsb_r0(ws[0]),
        lambda sym, ws: _render_get_sbyte(sym, _half_off(ws[0])),
    ),
    Template(
        "store-const-word",
        lambda ws: (len(ws) == 3 and ws[2] == _W_BX_LR
                    and _is_mov_r1_imm(ws[0]) and _is_str_r1(ws[1])),
        lambda sym, ws: _render_store_word(sym, ws[1] & 0xFFF, _signed(_imm12(ws[0]))),
    ),
    Template(
        "store-const-byte",
        lambda ws: (len(ws) == 3 and ws[2] == _W_BX_LR
                    and _is_mov_r1_imm(ws[0]) and _is_strb_r1(ws[1])),
        lambda sym, ws: _render_store_byte(sym, ws[1] & 0xFFF, _signed(_imm12(ws[0]))),
    ),
    Template(
        "far-word-getter",
        lambda ws: (len(ws) == 3 and ws[2] == _W_BX_LR
                    and _is_movw_r1(ws[0]) and _is_ldr_r0_r1(ws[1])),
        lambda sym, ws: _render_get_word(sym, _movw_imm(ws[0])),
    ),
    Template(
        "far-byte-getter",
        lambda ws: len(ws) == 3 and ws[2] == _W_BX_LR
        and _is_movw_r1(ws[0]) and _is_ldrb_r0_r1(ws[1]),
        lambda sym, ws: _render_get_byte(sym, _movw_imm(ws[0])),
    ),
)


def propose_rule(body: bytes | None, symbol: str) -> tuple[int, str, str] | None:
    """The matched rule and its proposal: ``(1-based number, rule name, source)``, or ``None``.

    The number is the rule's position in :data:`TEMPLATES`, so it is the ``rule #N`` the driver
    reports on a match; appending rules never renumbers the existing ones. Pure and deterministic
    (the same bytes always yield the same rule): the candidate is only a *proposal* — the gate is
    still the sole authority on a match.
    """
    if not body:
        return None
    words = _words(body)
    for number, template in enumerate(TEMPLATES, start=1):
        if template.match(words):
            return number, template.name, template.render(symbol, words)
    return None


def propose(body: bytes | None, symbol: str) -> str | None:
    """The templated translation unit for a recognized body, or ``None``.

    Deterministic and pure: the same bytes always yield the same source. The candidate is only a
    *proposal* — the caller must still run the byte gate, which is the sole authority on a match.
    """
    hit = propose_rule(body, symbol)
    return hit[2] if hit else None
