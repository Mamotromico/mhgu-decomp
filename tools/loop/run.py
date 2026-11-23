"""The reconstruction driver: one loop iteration per ledger entry.

It is glue, not a new capability — it wires the already-built, independently-testable parts
into the loop from ``docs/llm-harness-design.md`` → *The harness*::

    select -> bundle -> model -> write -> gate -> bank / record

Per entry it selects the next pending ``function`` (``worklist``), builds the annotated
context (``bundle``), asks the configured endpoint (``model``), writes the candidate to its
ledger-derived source path, and hands it to the **independent** byte gate
(``tools/ledger/bytegate.py``). The gate decides; the driver never claims a match itself.

Two rules shape the code, both from the design doc:

* **The gate is the only writer of ``verify``.** The driver always invokes the gate with
  ``--update``; the gate writes ``verify=match`` *only* on a real match, so the driver never
  edits that axis.
* **Containment is by construction.** The model only ever returns text. Every path the
  driver writes is derived **solely from the ledger** (``src/<module>/<group>.cpp`` and
  ``baserom/work/attempts/…``), guarded by a resolve-and-require-under-root check; model text
  is written to a file and never enters argv, a shell, ``eval``, or a compiler flag. Compilation
  is a fixed-argv, in-container subprocess.

On a **match** the candidate stays in ``src/`` and the gate has banked it. On a **near miss**
the draft is moved out of ``src/`` so it holds matched code only — never discarded
(``AGENTS.md``): every attempt is appended to the parent-linked log (``attempts.py``), and the
strictly-improving near-miss bank (``nearmiss.py``, under the eval pin) keeps the closest so far.

Every new attempt record carries an **experiment fingerprint** alongside the outcome (plan
step 1.3): the attempt ``kind`` (``plain``/``retry``/``repair``) and its ``parent``, the
provider/requested/server-reported model names and the server revision fingerprint, the exact
decoding parameters, hashes of the rendered prompt and of the retrieval (bundle) text, the
toolchain profile hash and the gate's comparison-rule version, plus latency, token counts,
finish reason, and ``cost_usd`` when a pricing table is configured. The fields record what
this attempt actually used, so a benchmark result can be reproduced or compared from the log
alone; records written before the fingerprint existed simply lack the fields.

Usage::

    python3 tools/loop/run.py                         # one entry (next pending, easiest first)
    python3 tools/loop/run.py --limit 5               # five entries
    python3 tools/loop/run.py --order addr            # select in the ledger's own order
    python3 tools/loop/run.py --entry 601a72e4        # a specific entry
    python3 tools/loop/run.py --entry 601a72e4 --attempts 5   # resample until it matches
    python3 tools/loop/run.py --entry 601a72e4 --attempts 5 --no-feedback  # plain resampling
    python3 tools/loop/run.py --from-bank --bank-max-divergences 3 --limit 20  # review close misses
    python3 tools/loop/run.py --matchable --limit 20   # only what the gate can verify today
    python3 tools/loop/run.py --repair --limit 20       # repair banked near misses (minimal edits)
    python3 tools/loop/run.py --repair --entry 601a72e4 --repair-rounds 6
    python3 tools/loop/run.py --dry-run                # select + bundle + prompt, no model
    python3 tools/loop/run.py --rebuild                # regenerate the bundle (Ghidra)
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))
sys.path.insert(0, str(REPO / "tools" / "loop"))

import attempts
import bundle
import complexity
import model as model_client
import nearmiss
import repair
import templates
import worklist
from ledgerlib import entry_key, read_entries

BYTEGATE = REPO / "tools" / "ledger" / "bytegate.py"
BUNDLE = REPO / "tools" / "loop" / "bundle.py"

SYSTEM = (
    "You reconstruct C/C++ functions from ARM (AArch32) disassembly for a byte-matching "
    "decompilation. Reply with a complete translation unit (the function definition and any "
    "declarations it needs). Never write inline assembly (__asm__/asm), volatile or otherwise, "
    "and never write machine instructions or top-level asm statements — the compiler must "
    "generate every instruction from ordinary C/C++. No prose, no Markdown fences.")

# A rendered bundle disassembly line: `    <addr>  <bytes>  <mnemonic> <operands> [; notes]`.
_BUNDLE_INSN = re.compile(r"^\s+([0-9a-f]{8})\s+([0-9a-f]+)\s+(\S+)\s*(.*)$")

# The by-value struct-copy guidance is only worth its weight when a block move is actually
# present, so it is included conditionally (see ``has_nonstack_block_move``).
_STRUCT_COPY_SECTION = (
    "A run of words moved by `ldmia`/`stmia` is ONE by-value struct copy, not per-word "
    "moves. Consecutive load/store-multiple blocks that walk contiguous addresses move a "
    "single object: add the words up (registers x blocks) to get its size, and give it a "
    "*named* type (two separately-written anonymous struct types are distinct and will not "
    "assign). Model the destination offset as a struct field and copy with one assignment.\n\n"
    "Worked example (a different function — it shows the idiom, not this answer):\n"
    "    ldmia r1!, {r2,r3,r12,lr}    ; 4 words from src, src += 16\n"
    "    add   r0, r0, #0x10\n"
    "    stmia r0!, {r2,r3,r12,lr}    ; 4 words to dst+0x10, dst += 16\n"
    "    ldmia r1, {r2,r3,r12,lr}     ; 4 words from src+16\n"
    "    stmia r0, {r2,r3,r12,lr}     ; 4 words to dst+0x20\n"
    "  is one 32-byte struct at offset 0x10 (4 + 4 = 8 words), copied by value:\n"
    "    struct Blob   { unsigned int w[8]; };\n"
    "    struct Holder { char pad[0x10]; Blob b; };\n"
    '    extern "C" void f(Holder *h, const Blob *src) { h->b = *src; }\n\n')


_BIT_OPS_SECTION = (
    "Bit-manipulation instructions come from a few exact C spellings. There is no builtin for "
    "`bfc`, `ubfx`, `sbfx` or `revsh` — `__builtin_arm_bfc`, `__builtin_arm_ubfx`, "
    "`__builtin_arm_sbfx` and `__builtin_arm_revsh` do not exist and will not compile — and "
    "`__builtin_arm_rbit` takes ONE argument.\n"
    "    rbit   -> __builtin_arm_rbit(x)      (ONE argument; returns the reversed u32)\n"
    "    clz    -> __builtin_clz(x)\n"
    "    rev    -> __builtin_bswap32(x)\n"
    "    rev16  -> __builtin_bswap16(x) on an `unsigned short` value (on a u32 it gives rev+lsr)\n"
    "    revsh  -> (short)__builtin_bswap16(x)\n"
    "    uxtb/sxtb/uxth/sxth -> cast to unsigned char / signed char / unsigned short / short\n"
    "    ubfx rX, rY, #lsb, #w -> (y >> lsb) & ((1u << w) - 1)\n"
    "    sbfx rX, rY, #lsb, #w -> (int)(y << (32 - lsb - w)) >> (32 - w)\n"
    "    bfi    -> (x & ~mask) | (v & mask), or a store into a bitfield of that width/offset\n"
    "    bfc    -> a store of 0 into a bitfield of that width/offset (the compiler emits `bic` "
    "instead when the mask fits that immediate)\n\n")

_BIT_OP_MNEMONICS = ("rbit", "clz", "rev", "rev16", "revsh", "ubfx", "sbfx", "bfi", "bfc")

# A pool load annotated with its target (``; = 0x… -> NAME``) is a data reference reached
# through the GOT. Without this guidance a model substitutes the address as a constant, which
# compiles to one instruction where the original has the whole indirection.
_GOT_REFERENCE_SECTION = (
    "A pc-relative load annotated `-> NAME` (for example `ldr r1, [0x6002b904]  ; = 0x… -> "
    "D_61730ebc`) is NOT a constant: it reaches NAME through the GOT, in two instructions "
    "(`ldr r1, [pc, #imm]` then `ldr r1, [pc, r1]`). Reproduce that as an ordinary C reference "
    "to a declared object, and let the compiler emit the indirection:\n"
    "    extern char NAME[];              // or a type/array that fits how it is used\n"
    "    ... = &NAME[offset];             // / *NAME / NAME.field, whichever the code does\n"
    "Do NOT write the address as a literal (`(void *)0x61730ebc`): that emits a plain "
    "constant and the bytes will not match. Keep the name exactly as annotated.\n\n")

_GOT_REFERENCE = re.compile(r"= 0x[0-9a-f]{8} -> ")


# A conditional return (`bxhi lr`, `bxeq lr`, ...) means the original kept the guard as a
# *branch*. clang 4.0.1 if-converts the small guarded body into predicated instructions
# instead (`addls`/`ldrls`, `moveq`), which is shorter than the original. There is no source
# shape that restores the branch (see AGENTS.md, "The inline-assembly rule"), and faking it
# with a barrier is forbidden, so this is guidance on what to *avoid* rather than a recipe.
_GUARDED_RETURN = re.compile(r"^\s+[0-9a-f]{8}\s+[0-9a-f]+\s+bx(hi|eq|ne|gt|lt|cs|cc|ge|le)\s+lr",
                             re.M)

_GUARDED_RETURN_SECTION = (
    "A conditional return (`bxhi lr`, `bxeq lr`, …) means the original kept this guard as a "
    "*real branch*. clang 4.0.1 tends to predicate a small guarded body instead "
    "(`addls`/`ldrls`, `moveq`), which is shorter than the original and will not match. Do NOT "
    "try to win those bytes with inline assembly — it is forbidden and is rejected before the "
    "gate. Write the most natural guard (`if (idx <= 7) { r = ...; } return r;`) and accept the "
    "mismatch; a candidate that fabricates the branch is worse than one that honestly fails.\n\n")

# `ldr rX,[rX,#D]` -> `bfc rX,#lsb,#width` -> an address use is "load a pointer, align it
# down, index through it". The masked value IS the base, so the C must treat it as a
# pointer; as integer arithmetic clang folds the constant and reorders `add` before `bfc`.
_MASK_FOR_ADDRESS_SECTION = (
    "A `bfc` on a loaded pointer that is then used as an address means \"load a pointer, "
    "clear its low bits, index through it\". The masked value is the BASE — express it as a "
    "pointer, not as integer arithmetic:\n"
    "    unsigned v = *(unsigned *)(p + 0xd7c);\n"
    "    v &= ~0xfu;                                  // the `bfc`\n"
    "    return *(float *)(v + 0x5c);                 // v is the base              (a load)\n"
    "    return (unsigned)((char *)v + 0x40);         // the same, returning an address\n"
    "Written as `return v + 0x40;` clang folds the constant and emits `add` before `bfc`, "
    "which does not match the original's `bfc`-then-`add`.\n\n")


_PREINDEXED = re.compile(
    r"^\s+[0-9a-f]{8}\s+[0-9a-f]+\s+(?:ldr|str)(?:b|h|sb|sh|d)?\s+r\d+,\s*\[[^\]]*\]!",
    re.M | re.I)

# `ldrh r2, [r0, r2]!` / `str r1, [r0, #-4]!` — pre-indexed with writeback. The C must update the
# base pointer *and* keep using it; written as `*(T *)((char *)p + imm)` clang drops the
# writeback (it is dead), so the body comes out one instruction short.
_PREINDEXED_SECTION = (
    "A `!` on a memory operand (`ldrh r2, [r0, r2]!`, `str r1, [r0, #0x18]!`) is a "
    "PRE-INDEXED WRITEBACK: the address is computed, used, AND stored back into the base "
    "register in one instruction. Reproduce it by assigning to the pointer inside the "
    "expression and then using the updated pointer again:\n"
    "    unsigned short v = *(unsigned short *)(p = (unsigned short *)((char *)p + 0x1a0));\n"
    "    *p = (unsigned short)(v | mask);            // the writeback is only kept because p "
    "is read here\n"
    "Written instead as `*(unsigned short *)((char *)p + 0x1a0)` the writeback is dead and "
    "clang drops it, so the body is one instruction short. For a post-indexed form "
    "(`[r0], #imm`) the pointer advances *after* the access.\n\n")


# Repair mode's extra instruction. It is appended *after* the previous translation unit so it
# is the last thing the model reads: the candidate is already the right length, so the job is
# a minimal edit, and the one honest escape is to say the remaining bytes are register
# allocation (which no source shape controls).
_REPAIR_SECTION = (
    "\n## This is a REPAIR pass\n\n"
    "The translation unit above was your previous answer. It already compiles to exactly the "
    "original body length; only the instructions listed as differing are wrong. Make the "
    "SMALLEST edit that fixes them — change one expression, one type, or the order of two "
    "independent statements — and return the whole translation unit again. Do not restructure "
    "the function, do not rename anything, do not rewrite parts that already match, and never "
    "change what the code computes.\n\n"
    "If every remaining difference is only WHICH REGISTER holds a value (the mnemonics, "
    "immediates and widths all agree), the source is already correct and the rest is the "
    "original compiler's register allocation. In that case reply with exactly `UNREACHABLE` "
    "and nothing else.\n\n")


def has_preindexed(bundle_text: str) -> bool:
    """Whether the disassembly has a pre-indexed load/store with writeback (see the section)."""
    return bool(_PREINDEXED.search(bundle_text))


def has_guarded_return(bundle_text: str) -> bool:
    """Whether the disassembly returns conditionally (a guard the original did not predicate)."""
    return bool(_GUARDED_RETURN.search(bundle_text))


def has_mask_for_address(bundle_text: str) -> bool:
    """Whether a masked register is used as an address (the align-down-then-index idiom).

    Walks the parsed instructions: after a ``bfc rd`` the next one or two instructions use
    ``rd`` either as a memory base (``[rd]``/``[rd, …]``, which also covers ``vldr s0,
    [rd, #imm]`` where the base is the *second* operand) or as the first operand of an
    ``add``/``sub`` (address arithmetic). Either way the masked value is a base.
    """
    insns = []
    for line in bundle_text.splitlines():
        m = _BUNDLE_INSN.match(line)
        if m:
            insns.append((m.group(3), m.group(4).strip()))
    for i, (mnemonic, operands) in enumerate(insns):
        if not mnemonic.startswith("bfc"):
            continue
        reg = operands.split(",")[0].strip()
        if not (reg.startswith("r") and reg[1:].isdigit()):
            continue
        for next_mnemonic, next_operands in insns[i + 1:i + 3]:
            if f"[{reg}]" in next_operands or f"[{reg}," in next_operands:
                return True
            if next_mnemonic.startswith(("add", "sub")) \
                    and next_operands.startswith(reg + ","):
                return True
    return False



def has_got_reference(bundle_text: str) -> bool:
    """Whether the bundle resolves a pool word to a name (a data reference)."""
    return bool(_GOT_REFERENCE.search(bundle_text))


def has_bit_op(bundle_text: str) -> bool:
    """Whether the bundle disassembly contains a bit-manipulation instruction.

    Only the ones with a non-obvious C spelling are listed, so the section stays out of the
    prompt for the majority of functions (a plain `uxtb` from a cast is common and already
    handled without help).
    """
    for line in bundle_text.splitlines():
        m = _BUNDLE_INSN.match(line)
        if m and m.group(3).startswith(_BIT_OP_MNEMONICS):
            return True
    return False


def has_nonstack_block_move(bundle_text: str) -> bool:
    """Whether the bundle disassembly has an ``ldm``/``stm`` whose base is not the stack.

    The by-value struct-copy section only pays off when such a block move is present; the
    ``push``/``pop`` save every non-leaf function has is sp-based (or printed as ``push``/``pop``)
    and must not trigger it. This keeps the prompt's strongest worked example aligned with the
    idiom's ~1% incidence (see ``docs/llm-harness-design.md`` → *Template growth is measured*).
    """
    for line in bundle_text.splitlines():
        m = _BUNDLE_INSN.match(line)
        if not m:
            continue
        mnemonic, operands = m.group(3), m.group(4)
        if mnemonic.startswith(("ldm", "stm")) and "sp" not in operands:
            return True
    return False


@dataclass
class Feedback:
    """The previous attempt's outcome, fed into the next prompt (a retry only).

    Built from the attempt log (:func:`feedback_from_record`), so it reflects what the gate
    actually said, never a re-derivation. ``candidate`` is the previous translation unit (for
    the model to edit); ``diff_words``/``compile_error`` are the actionable divergence.
    """

    outcome: str
    status: str | None = None
    diff_count: int | None = None
    diff_words: list = field(default_factory=list)
    candidate: str | None = None
    compile_error: str | None = None
    compiled_body: int | None = None
    expected_body: int | None = None


def parse_reference_instructions(bundle_text: str, base_addr: str) -> dict[int, str]:
    """Map body-relative offset -> original instruction text, from the bundle's disassembly.

    The bundle lists absolute addresses; ``base_addr`` is the entry address, so the offset of a
    line is ``addr - base_addr`` — the same frame the gate's ``diff_words`` offsets use. Only the
    ``## disassembly`` section is read (the later ``## calls`` section is ignored).
    """
    base = int(base_addr, 16)
    out: dict[int, str] = {}
    inside = False
    for line in bundle_text.splitlines():
        if line.startswith("## "):
            inside = line.startswith("## disassembly")
            continue
        if not inside:
            continue
        m = _BUNDLE_INSN.match(line)
        if m:
            out[int(m.group(1), 16) - base] = f"{m.group(3)} {m.group(4)}".strip()
    return out


_COND_NAME = ("eq", "ne", "cs", "cc", "mi", "pl", "vs", "vc",
              "hi", "ls", "ge", "lt", "gt", "le", "al", "nv")


def describe_word_diff(got: str, want: str) -> str:
    """Say in words how the candidate's A32 word differs from the original's, or ``""``.

    ``got``/``want`` are the gate's byte-order hex strings (memory order, as they appear in the
    object and in the image). The point is to turn "got 0100a031 want 0100a091" — which the model
    cannot decode — into "condition code differs: yours `cc`, original `ls`", so a near-miss
    becomes an edit it can actually make. Only the checks that are unambiguous on an A32 word are
    attempted; anything else returns ``""`` rather than a guess.
    """
    try:
        g = int.from_bytes(bytes.fromhex(got), "little")
        w = int.from_bytes(bytes.fromhex(want), "little")
    except ValueError:
        return ""
    if g == w or len(got) != 8:
        return ""
    if (g ^ w) & 0xF0000000:
        return (f"condition code differs: yours `{_COND_NAME[(g >> 28) & 0xF]}`, "
                f"original `{_COND_NAME[(w >> 28) & 0xF]}` (check `<` vs `<=` and signed vs "
                f"unsigned in the comparison)")
    # Single data transfer immediate/register form: bits 27-26 == 01.
    if (g & 0x0C000000) == 0x04000000 and (w & 0x0C000000) == 0x04000000:
        if (g ^ w) & 0x00100000:
            return ("load vs store: yours is a " + ("load" if g & 0x00100000 else "store") +
                    ", the original is a " + ("load" if w & 0x00100000 else "store"))
        if (g ^ w) & 0x00400000:
            return "byte vs word access (the original uses a different width)"
        if (g ^ w) & 0x00200000:
            if w & 0x00200000:
                return ("the original writes the address back (`!`, pre-indexed); yours does "
                        "not — assign to the pointer inside the expression and then use the "
                        "updated pointer again")
            return "yours writes the address back (`!`); the original does not"
        if (g ^ w) & 0x00800000:
            return "the offset sign differs (positive vs negative displacement)"
    # Block transfer: `stm` vs `ldm` (bit 20).
    if (g & 0x0E000000) == 0x08000000 and (w & 0x0E000000) == 0x08000000:
        if (g ^ w) & 0x00100000:
            return ("load vs store: yours is a " + ("load (`ldm`)" if g & 0x00100000
                                                    else "store (`stm`)")
                    + ", the original is a " + ("load (`ldm`)" if w & 0x00100000
                                                else "store (`stm`)"))
    # Halfword / signed transfer (bits 27-25 == 000 with the 0x90 misc discriminator).
    if (g & 0x0E000090) == 0x00000090 and (w & 0x0E000090) == 0x00000090:
        if (g ^ w) & 0x00100000:
            return ("load vs store: yours is a " + ("load" if g & 0x00100000 else "store")
                    + ", the original is a " + ("load" if w & 0x00100000 else "store"))
        if (g ^ w) & 0x00200000:
            if w & 0x00200000:
                return ("the original writes the address back (`!`, pre-indexed); yours does "
                        "not — assign to the pointer inside the expression and then use the "
                        "updated pointer again")
            return "yours writes the address back (`!`); the original does not"
    if (g ^ w) & 0x0FFFFFFF == 0:
        return ""
    if not ((g ^ w) & 0x0FFFF000) and ((g ^ w) & 0xFFF):
        return "a different (or differently encoded) immediate value"
    return ""


def feedback_section(entry: dict, bundle_text: str,
                     feedback: "Feedback | None", repair_pass: bool = False) -> str:
    """Render the retry guidance appended to the prompt; empty when there is no feedback.

    A mismatch names the exact instructions that differ (offset, candidate bytes, reference
    bytes, and the reference mnemonic when the bundle carries it); a compile error quotes the
    compiler. The previous translation unit is included so the model edits rather than regenerates.

    ``repair_pass`` appends the repair-mode instruction (a minimal edit, or ``UNREACHABLE`` for
    a register-allocation-only difference) *after* the previous translation unit, so it is the
    last thing the model reads.
    """
    if feedback is None:
        return ""
    if feedback.compile_error:
        body = (
            "## Previous attempt did not compile\n\n"
            "The compiler rejected the last translation unit:\n\n"
            "```\n" + feedback.compile_error.strip()[-1200:] + "\n```\n\n"
            "Return a corrected translation unit that compiles.")
    else:
        ref = parse_reference_instructions(bundle_text, entry["addr"])
        rows = []
        for w in feedback.diff_words:
            insn = ref.get(w["offset"])
            hint = describe_word_diff(w["got"], w["want"])
            rows.append(f"    +0x{w['offset']:x}  got {w['got']}  want {w['want']}"
                        + (f"   ; original: {insn}" if insn else "")
                        + (f"   <- {hint}" if hint else ""))
        if not rows:
            rows.append(f"    (compiled body {feedback.status}; see the disassembly above)")
        size_note = ""
        if feedback.status == "body-length" and feedback.compiled_body \
                and feedback.expected_body:
            delta = feedback.compiled_body - feedback.expected_body
            if delta > 0:
                size_note = (f"Your candidate compiled to {feedback.compiled_body} B but the "
                             f"original body is {feedback.expected_body} B — "
                             f"{delta} BYTES TOO LONG ({delta // 4} instruction(s) too many). "
                             "The differing instructions listed below only cover the prefix; "
                             "find the surplus instruction(s) in your translation unit and "
                             "remove them (a separate `add` before a load is the usual cause).\n\n")
            else:
                size_note = (f"Your candidate compiled to {feedback.compiled_body} B but the "
                             f"original body is {feedback.expected_body} B — "
                             f"{-delta} BYTE(S) TOO SHORT; the compiler collapsed an operation "
                             "you wrote as several steps.\n\n")
        body = (
            size_note
            + "## Previous attempt did not match\n\n"
            "The last candidate compiled, but the machine code differs from the original "
            f"({feedback.diff_count} differing byte(s)). Fix ONLY the instructions below; keep "
            "the rest of the translation unit unchanged. `got` is your bytes, `want` is the "
            "original's. The logic must stay EXACTLY the same — never change what the code "
            "computes to chase a byte. If the only difference is which register holds a value, "
            "your source is already correct; try an equivalent phrasing (a different local's "
            "type, reordering independent statements, a pointer instead of an index) rather "
            "than altering the computation:\n\n"
            + "\n".join(rows))
    parts = [body]
    if feedback.candidate:
        parts.append("--- your previous translation unit ---\n"
                     + feedback.candidate.strip() + "\n--- end ---")
    if repair_pass:
        parts.append(_REPAIR_SECTION.strip())
    return "\n\n".join(parts) + "\n"


def feedback_from_record(record: dict | None, store_dir: Path) -> Feedback | None:
    """The retry feedback for a recorded attempt, or ``None`` if it is not actionable.

    Only a ``mismatch`` or ``error`` carries feedback (a ``match`` needs no retry). The previous
    candidate blob, if present, is read back so the model can revise it.
    """
    if not record or record.get("outcome") not in ("mismatch", "error"):
        return None
    candidate = None
    rel = record.get("candidate")
    if rel:
        blob = Path(store_dir) / rel
        if blob.exists():
            candidate = blob.read_text()
    if record["outcome"] == "error":
        return Feedback("error", candidate=candidate,
                        compile_error=record.get("gate_output") or "")
    compiled, expected = _body_sizes(record.get("gate_output") or "")
    return Feedback("mismatch", status=record.get("gate_status"),
                    diff_count=record.get("diff_count"),
                    diff_words=record.get("diff_words") or [], candidate=candidate,
                    compiled_body=compiled, expected_body=expected)


_BODY_SIZES = re.compile(r"compiled (\d+) B, original (\d+) B")


def _body_sizes(gate_output: str) -> tuple[int | None, int | None]:
    """The compiled and reference body sizes a ``body-length`` verdict reports, if present."""
    m = _BODY_SIZES.search(gate_output)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


@dataclass
class Layout:
    """The fixed paths one run reads from and writes to (all repo-relative)."""

    ledger: Path = REPO / "config" / "main" / "ledger.tsv"
    inventory: Path = bundle.DEFAULT_INVENTORY
    nso: Path = bundle.DEFAULT_NSO
    context: Path = REPO / "baserom" / "work" / "context"
    src_root: Path = REPO / "src"
    build_config: Path = REPO / "config" / "build.json"
    toolchain: Path = REPO / "config" / "toolchain.json"
    work: Path = REPO / "baserom" / "work"
    model_config: Path = REPO / "config" / "model.json"


# --- pure helpers (unit-tested) -------------------------------------------------------

def safe_draft_path(entry: dict, src_root: Path) -> Path:
    """The one source path a candidate for ``entry`` may be written to.

    Derived **solely from the ledger**; a module or group containing a path separator or
    ``..`` is refused outright, so ledger data can never escape the source root.
    """
    module, group = entry["module"], entry["group"]
    for part in (module, group):
        if not part or "/" in part or "\\" in part or part in (".", ".."):
            raise ValueError(f"unsafe ledger path component: {part!r}")
    return Path(src_root) / module / f"{group}.cpp"


def ensure_under(path: Path, root: Path) -> Path:
    """Resolve ``path`` and require it to live under ``root``; return the resolved path."""
    resolved, resolved_root = Path(path).resolve(), Path(root).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"refusing to write outside {resolved_root}: {resolved}")
    return resolved


def context_path(layout: Layout, entry: dict) -> Path:
    return layout.context / entry["module"] / f"{entry['addr']}.md"


def attempt_store(layout: Layout) -> Path:
    return layout.work / "attempts"


def bank_path(layout: Layout) -> Path:
    return layout.work / "nearmiss" / "bank.json"


def group_is_single(entries: list[dict], module: str, group: str) -> bool:
    """Whether exactly one ``function`` entry uses this ``(module, group)`` translation unit.

    A draft may only be removed from ``src/`` when the file is *this* entry's alone; a merged
    translation unit (several entries sharing a group) must be left untouched.
    """
    return sum(1 for e in entries
               if e["module"] == module and e["group"] == group
               and e["kind"] == "function") == 1


def build_prompt(entry: dict, bundle_text: str, feedback: "Feedback | None" = None,
                 repair_pass: bool = False) -> str:
    """The user prompt: the required symbol plus the whole context bundle.

    The instructions are load-bearing: an early pilot had the model reproduce the disassembly
    as inline ``__asm__`` (which cannot match the surrounding codegen and, as written, did not
    even compile). Plain C/C++ is required; an ``asm`` label is only for a symbol that is not a
    valid identifier. A later pilot modelled a run of words as two *anonymous* structs, which is
    ill-formed (they are distinct types); the instructions now require a named type. The
    struct-copy guidance is now **conditional** (``has_nonstack_block_move``): it is included
    only when the bundle actually carries a non-stack ``ldm``/``stm``, so a rare idiom no longer
    dominates the prompt (see ``docs/llm-harness-design.md`` → *Template growth is measured*).
    The bit-manipulation section is conditional on the same principle (``has_bit_op``): it lists
    only spellings verified against the pinned compiler, after models guessed builtins that do
    not exist (``__builtin_arm_bfc``, ``__builtin_arm_ubfx``) and a two-argument ``rbit``.

    ``feedback`` (a retry only, so ``None`` on the first attempt) appends the previous attempt's
    divergence — the exact instructions that differ, or the compiler error — so a retry improves
    on the previous try instead of resampling the identical prompt. With ``feedback is None`` the
    output is byte-identical to the pre-feedback prompt.
    """
    name = entry["name"]
    if name.isidentifier():
        symbol = f'Define it with `extern "C"` so the object symbol is exactly `{name}`.'
    else:
        symbol = (f"`{name}` is not a valid C++ identifier; give the function a C++-legal name "
                  f'and bind it to the exact symbol with a trailing asm("{name}") on its '
                  f"declaration.")
    copy_section = _STRUCT_COPY_SECTION if has_nonstack_block_move(bundle_text) else ""
    bit_section = _BIT_OPS_SECTION if has_bit_op(bundle_text) else ""
    got_section = _GOT_REFERENCE_SECTION if has_got_reference(bundle_text) else ""
    guard_section = _GUARDED_RETURN_SECTION if has_guarded_return(bundle_text) else ""
    mask_section = _MASK_FOR_ADDRESS_SECTION if has_mask_for_address(bundle_text) else ""
    preindex_section = _PREINDEXED_SECTION if has_preindexed(bundle_text) else ""
    return (
        f"Write ordinary C or C++ whose compiled machine code reproduces the function below "
        f"exactly under the pinned toolchain. Reason about the function's *behaviour*, not its "
        f"registers: the register allocation was the original compiler's choice and yours will "
        f"differ. Do NOT use inline assembly — ``__asm__``/``asm``, ``asm volatile``, or a "
        f"top-level asm() statement — and never write machine instructions by hand: the "
        f"compiler must emit every instruction from ordinary C/C++. A candidate containing any "
        f"asm other than a declarator symbol binding (`void f(void) asm(\"name\");`, used only "
        f"to fix an object symbol name) is rejected before the gate. The ARM "
        f"AAPCS ABI applies: r0-r3 carry the arguments and r0 the result; the prologue and "
        f"epilogue are generated for you.\n\n"
        f"{got_section}"
        f"{copy_section}"
        f"{guard_section}"
        f"{preindex_section}"
        f"{mask_section}"
        f"Load and store memory through a TYPED pointer: `*(unsigned *)(p + 0x1d8)`, "
        f"`*(float *)(v + 0x4c)`. Do NOT copy with `__builtin_memcpy` from a `char *` — "
        f"clang cannot assume alignment there and emits four byte-sized loads/stores instead "
        f"of one word access, which lengthens the body and can never match.\n\n"
        f"Take each struct's layout from the instructions that touch it. A field's offset is the "
        f"displacement in its load/store — `ldrb r3, [r0, #0x20]` puts that field at +0x20. An "
        f"array element's size is the pointer-increment constant — `add r0, r0, #0x30` means "
        f"sizeof(element) is exactly 0x30; pad the struct so its size equals that constant. Fields "
        f"need not be adjacent — place each at its exact displacement and insert explicit padding "
        f"for the gaps; do not assume one field immediately follows another. Do not guess any of "
        f"these values. For example, if a field loads at `[r0, #0x58]` and the previous field is "
        f"a 4-byte value at `[r0, #0x40]`, the second field's offset is 0x58 (not 0x44), so pad "
        f"0x58 - 0x44 = 0x14 bytes: the displacement is the offset, and the padding is whatever "
        f"makes the field land exactly there. If a padding expression would come out negative, "
        f"you subtracted the wrong way round: subtract the smaller displacement from the larger.\n\n"
        f"{bit_section}"
        f"{symbol}\n"
        f"Reply with the translation unit only — no prose, no Markdown fences.\n\n"
        f"{bundle_text}\n"
        f"{feedback_section(entry, bundle_text, feedback, repair_pass)}"
    )


def repair_prompt(entry: dict, bundle_text: str, source: str, report: dict | None,
                  gate_output: str = "") -> str:
    """The repair-mode prompt for the current best candidate.

    It is the ordinary task prompt plus a :class:`Feedback` describing this candidate's
    divergence — which reuses the tested diff rows, the reference mnemonics and the
    ``describe_word_diff`` hints — plus the repair instruction. ``report`` is ``None`` when the
    candidate did not compile; the compiler's message is then the feedback instead.
    """
    if report is None and not gate_output:
        # A dry run has not compiled the seed, so there is no divergence to report yet; show
        # the candidate and the repair instruction, and leave the diff for the real session.
        return (build_prompt(entry, bundle_text, None)
                + "\n--- your previous (banked) translation unit ---\n"
                + source.strip() + "\n--- end ---\n\n" + _REPAIR_SECTION.strip() + "\n")
    if report is None:
        feedback = Feedback("error", candidate=source, compile_error=gate_output or "")
    else:
        feedback = Feedback("mismatch", status=report.get("status"),
                            diff_count=report.get("diff_count"),
                            diff_words=report.get("diff_words") or [], candidate=source,
                            compiled_body=report.get("cand_len"),
                            expected_body=report.get("ref_len"))
    return build_prompt(entry, bundle_text, feedback, repair_pass=True)


def bundle_argv(layout: Layout, entry: dict, body: int) -> list[str]:
    return [sys.executable, str(BUNDLE), entry["module"], entry["addr"],
            "--ledger", str(layout.ledger), "--inventory", str(layout.inventory),
            "--nso", str(layout.nso), "--out", str(layout.context),
            "--body", str(body)]


def gate_argv(layout: Layout, entry: dict, body: int | None,
              report: Path | None = None) -> list[str]:
    """The byte-gate invocation. Fixed argv: no model text ever reaches it.

    ``body`` is the validated instruction-plus-pool extent. ``None`` omits ``--body`` only
    for an explicit fail-closed path; the gate then reports ``missing-body``.
    """
    argv = [sys.executable, str(BYTEGATE), entry["module"], entry["addr"],
            "--src-root", str(layout.src_root), "--ledger", str(layout.ledger),
            "--toolchain", str(layout.toolchain), "--build-config", str(layout.build_config),
            "--nso", str(layout.nso), "--update"]
    if body is not None:
        argv += ["--body", str(body)]
    if report is not None:
        argv += ["--report", str(report)]
    return argv


def attempted_counts(layout: Layout) -> dict[tuple[str, str], int]:
    """How many attempts each entry already has in the log, across every run.

    ``--attempts`` is per invocation, so without this an entry that never matches stays at the
    front of the queue and is re-attempted on every run. Served from the attempt index rather
    than a full log scan. A corrupt log is a warning, not a failure: the filter is a
    convenience, not a correctness gate.
    """
    try:
        return attempts.attempt_counts(attempt_store(layout))
    except attempts.AttemptError as e:
        print(f"warning: {e}; --skip-attempted ignored", file=sys.stderr)
        return {}


def bank_priorities(layout: Layout) -> dict[tuple[str, str], list[int]]:
    """The near-miss bank as ``(module, addr) -> closeness``, current-pin records only.

    A record written under a different eval pin is not comparable (``nearmiss.best``), so it is
    dropped here rather than ordered against numbers from another metric/compiler.
    """
    try:
        bank = nearmiss.load_bank(bank_path(layout))
    except ValueError as e:
        print(f"warning: {e}; --from-bank ignored", file=sys.stderr)
        return {}
    try:
        pin = nearmiss.eval_pin(layout.toolchain)
    except ValueError as e:
        print(f"warning: {e}; --from-bank ignored", file=sys.stderr)
        return {}
    priorities: dict[tuple[str, str], list[int]] = {}
    for record in bank.get("records", {}).values():
        if record.get("pin") != pin or not record.get("closeness"):
            continue
        priorities[(record.get("module"), record.get("addr"))] = list(record["closeness"])
    return priorities


def bank_seeds(layout: Layout) -> dict[tuple[str, str], tuple[str, str | None]]:
    """The banked near-miss candidate **source** for each entry, current pin only.

    The bank records the closeness and the ``attempt_id`` of the best near miss; the source
    itself lives in the attempt store, so repairing needs the log record to find the blob. A
    record from another eval pin is skipped — its candidate was judged by a different gate, so
    the numbers are not comparable (``tools/ledger/regate_candidates.py`` is the tool for
    re-judging those). Returns ``(module, addr) -> (source_text, attempt_id)``.
    """
    try:
        bank = nearmiss.load_bank(bank_path(layout))
        pin = nearmiss.eval_pin(layout.toolchain)
    except ValueError as e:
        print(f"warning: {e}; --repair ignored", file=sys.stderr)
        return {}
    store = attempt_store(layout)
    wanted = [r.get("attempt_id") for r in bank.get("records", {}).values()
              if r.get("pin") == pin and r.get("attempt_id") is not None]
    try:
        by_id = attempts.records_by_id(store, wanted)
    except attempts.AttemptError as e:
        print(f"warning: {e}; --repair ignored", file=sys.stderr)
        return {}
    seeds: dict[tuple[str, str], tuple[str, str | None]] = {}
    for record in bank.get("records", {}).values():
        if record.get("pin") != pin:
            continue
        attempt_id = record.get("attempt_id")
        owner = by_id.get(attempt_id)
        if not owner or not owner.get("candidate"):
            continue
        blob = store / owner["candidate"]
        if not blob.exists():
            continue
        seeds[(record.get("module"), record.get("addr"))] = (blob.read_text(), attempt_id)
    return seeds


def bank_seed(layout: Layout, module: str,
              addr: str) -> tuple[str, str | None] | None:
    """One entry's banked candidate source (a per-entry view over :func:`bank_seeds`)."""
    return bank_seeds(layout).get((module, addr))


def matchable_filter(layout: Layout, text: bytes | None):
    """A predicate: can the byte gate verify this entry's body today?

    The gate resolves branch/call relocations but not literal-pool words or jump tables
    (``complexity.gateable``), so a body that reads a pool word or builds an address is
    excluded. ``None`` when the reference ``.text`` is unavailable (no filter possible).
    """
    if text is None:
        print("warning: reference .text unavailable for --matchable; filter ignored",
              file=sys.stderr)
        return None
    sizes = (bundle.parse_inventory(layout.inventory.read_text())
             if layout.inventory.exists() else {})

    def ok(entry: dict) -> bool:
        body = complexity.body_of(text, entry["addr"], sizes.get(entry["addr"], 0))
        return complexity.gateable(body)

    return ok


def select_next(entries: list[dict], layout: Layout, *, skip_existing: bool,
                done: set[tuple[str, str]],
                key=None, attempted: dict[tuple[str, str], int] | None = None,
                skip_attempted: int | None = None,
                bank: dict[tuple[str, str], list[int]] | None = None,
                bank_max_len_delta: int | None = None,
                bank_max_divergences: int | None = None,
                tier_key=None, max_tier: int | None = None,
                matchable=None) -> dict | None:
    """The next pending function not already handled this run.

    ``key`` is the optional difficulty ordering (``complexity.make_key``); ``None`` keeps the
    ledger's own ``(module, addr)`` order. Both stay deterministic, so a resume is unaffected.

    ``skip_attempted`` drops entries that already drew that many attempts across *previous*
    runs (``attempted`` is the per-entry count from the log), so a run advances through the
    ledger instead of grinding the same stuck entries at the front of the queue.

    ``bank`` (``--from-bank``) restricts the queue to entries with a comparable near-miss and
    orders it closest-first, so a run revisits the candidates that were one instruction away
    instead of paying for fresh functions. ``bank_max_len_delta`` / ``bank_max_divergences``
    bound how close a record must be; the closeness ordering itself overrides ``key``.

    ``max_tier`` (``--max-tier``) drops entries whose ``complexity`` tier exceeds it. ``matchable``
    (``--matchable``) drops entries the gate cannot verify at all today — a body whose only
    relocations are branches is matchable, one that reads a literal pool or builds a jump-table
    address is not (``complexity.gateable``). It is the stronger filter of the two; the tier is a
    difficulty ranking, not a verdict.
    """
    queue = worklist.select(entries, kind="function", verify="none", key=key)
    if max_tier is not None and tier_key is not None:
        queue = [e for e in queue if tier_key(e)[0] <= max_tier]
    if matchable is not None:
        queue = [e for e in queue if matchable(e)]
    if skip_existing:
        queue = [e for e in queue if not worklist.source_path(e, layout.src_root).exists()]
    if skip_attempted is not None and attempted:
        queue = [e for e in queue if attempted.get(entry_key(e), 0) < skip_attempted]
    if bank is not None:
        queue = [e for e in queue if entry_key(e) in bank
                 and (bank_max_len_delta is None or bank[entry_key(e)][0] <= bank_max_len_delta)
                 and (bank_max_divergences is None
                      or bank[entry_key(e)][1] <= bank_max_divergences)]
        queue.sort(key=lambda e: (bank[entry_key(e)], e["module"], e["addr"]))
    for entry in queue:
        if entry_key(entry) not in done:
            return entry
    return None


def complexity_key(layout: Layout, text: bytes | None):
    """The easy-first selector key from a reference ``.text``, or ``None`` for address order."""
    if text is None:
        print("warning: reference .text unavailable for --order easiest; using address order",
              file=sys.stderr)
        return None
    sizes = (bundle.parse_inventory(layout.inventory.read_text())
             if layout.inventory.exists() else {})
    blocks = complexity.load_blocks(layout.inventory.with_name("inventory.blocks.tsv"))
    return complexity.make_key(text, sizes, blocks)


def resolve_entry(entries: list[dict], module: str, addr: str) -> dict:
    """Find the ``--entry`` target; ``addr`` is normalized, ``module`` defaults to main."""
    return bundle.find_entry(entries, module, addr.lower().removeprefix("0x").zfill(8))


# --- impure steps ---------------------------------------------------------------------

def run_subprocess(argv: list[str]) -> tuple[int, str]:
    result = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout + result.stderr


def resolve_body(layout: Layout, entry: dict, override: int | None) -> tuple[int, str]:
    sizes = (bundle.parse_inventory(layout.inventory.read_text())
             if layout.inventory.exists() else {})
    return bundle.resolve_body(entry, sizes, override)


def prompt_fingerprint(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def file_sha256(path: Path | None) -> str | None:
    """The content fingerprint of a config file, or ``None`` when it cannot be read.

    Records carry the toolchain profile's hash (never its path, which varies by checkout)
    so a benchmark result can be tied to the exact compiler pin that produced it.
    """
    if path is None:
        return None
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return None


_DECODE_PARAMS = ("temperature", "max_tokens", "seed", "reasoning_effort")


def decoding_params(model) -> dict:
    """The sampling parameters the client will actually send, for the attempt record.

    Only set parameters are recorded (a missing key means "the server/preset default was
    in force"), so the record reflects the exact decoding configuration of this attempt.
    """
    return {name: getattr(model, name, None) for name in _DECODE_PARAMS
            if getattr(model, name, None) is not None}


def completion_fields(model, prompt_tokens, completion_tokens, finish_reason="",
                      system_fingerprint="") -> dict:
    """The experiment-fingerprint fields describing *how the model was asked*.

    Shared by a plain attempt and a repair round. ``provider``/``requested_model`` are the
    configured endpoint and model name; ``model`` on the record itself stays the
    server-reported name from the completion, so a router that silently served a different
    revision is visible. ``cost_usd`` appears only when a pricing table is configured and
    the usage counts are present — absent means "not recorded", never "free".
    """
    fields = {
        "provider": getattr(model, "endpoint", None),
        "requested_model": getattr(model, "model", None),
        "decoding": decoding_params(model),
        "finish_reason": finish_reason or None,
    }
    cost = model_client.completion_cost(prompt_tokens, completion_tokens,
                                        getattr(model, "pricing", None))
    if cost is not None:
        fields["cost_usd"] = cost
    if system_fingerprint:
        fields["system_fingerprint"] = system_fingerprint
    return fields


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=Layout.ledger)
    ap.add_argument("--inventory", type=Path, default=Layout.inventory)
    ap.add_argument("--nso", type=Path, default=Layout.nso)
    ap.add_argument("--context", type=Path, default=Layout.context)
    ap.add_argument("--src-root", type=Path, default=Layout.src_root)
    ap.add_argument("--work", type=Path, default=Layout.work)
    ap.add_argument("--model-config", type=Path, default=Layout.model_config)
    ap.add_argument("--toolchain", type=Path, default=Layout.toolchain,
                    help="compiler profile for the byte gate (default: config/toolchain.json — "
                         "clang 4.0.1, the only supported pin)")
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--endpoint", default=None)
    ap.add_argument("--model-name", default=None)
    ap.add_argument("--proxy", default=None)
    ap.add_argument("--timeout", type=float, default=None,
                    help="model request timeout in seconds (a cold load can be slow)")
    ap.add_argument("--temperature", type=float, default=None,
                    help="sampling temperature override (omit to use the server/preset default)")
    ap.add_argument("--max-tokens", type=int, default=None,
                    help="output-token cap override; the config's value (sized for the local "
                         "model) is otherwise reused against any --base-url")
    ap.add_argument("--reasoning-effort", default=None,
                    help="reasoning-effort override; 'none' disables a provider's thinking mode "
                         "(DeepSeek enables it by default and bills it inside max_tokens)")
    ap.add_argument("--seed", type=int, default=None, help="sampling seed override (optional)")
    ap.add_argument("--body", type=int, default=None)
    ap.add_argument("--module", default="main", help="module for --entry (default: main)")
    ap.add_argument("--entry", default=None, help="target one ledger address (in --module)")
    ap.add_argument("--limit", type=int, default=1, help="entries to process (default 1)")
    ap.add_argument("--order", choices=("easiest", "addr"), default="easiest",
                    help="auto-select order when no --entry: 'easiest' (difficulty, default) "
                         "or 'addr' (the ledger's own order)")
    ap.add_argument("--attempts", type=int, default=1,
                    help="attempts per entry, stopping early on a match (default 1)")
    ap.add_argument("--skip-attempted", type=int, default=None, metavar="N",
                    help="skip entries that already drew N or more attempts across previous "
                         "runs (--attempts is per run, so without this a stuck entry stays at "
                         "the front of the queue forever); e.g. 1 = only fresh entries, "
                         "4 = stop revisiting entries that never converge")
    ap.add_argument("--compile-attempts", type=int, default=2,
                    help="separate budget for non-compiling candidates: stop retrying an entry "
                         "once this many attempts produced code clang rejected (default 2)")
    ap.add_argument("--from-bank", action="store_true",
                    help="revisit the near-miss bank instead of fresh functions: only entries "
                         "with a current-pin near miss, ordered closest-first (overrides "
                         "--order); use with --bank-max-len-delta/--bank-max-divergences")
    ap.add_argument("--bank-max-len-delta", type=int, default=0, metavar="N",
                    help="with --from-bank, keep only records whose candidate length is within "
                         "N bytes of the body (default 0 = same length, the reviewable ones)")
    ap.add_argument("--bank-max-divergences", type=int, default=None, metavar="N",
                    help="with --from-bank, keep only records with at most N differing words "
                         "(omit for no cap)")
    ap.add_argument("--max-tier", type=int, default=None, metavar="N",
                    help="only entries whose complexity tier is <= N (a *difficulty* ranking; "
                         "0 = clean leaves). For 'what the gate can verify', use --matchable")
    ap.add_argument("--matchable", action=argparse.BooleanOptionalAction, default=True,
                    help="only entries the gate can verify today: branch/call relocations are "
                         "resolved, literal-pool words, jump tables and linker veneers are not "
                         "(complexity.gateable). ON by default — such an entry cannot match, so "
                         "attempting it only pollutes the match rate; pass --no-matchable to "
                         "override (e.g. to inspect a specific body)")
    ap.add_argument("--no-feedback", dest="feedback", action="store_false",
                    help="on a retry, do not feed the previous attempt's divergence back into "
                         "the prompt (resample the base prompt; also disables the stall stop)")
    ap.add_argument("--repair", action="store_true",
                    help="repair mode: seed each entry from its banked near miss and ask the "
                         "model for a minimal edit of that exact translation unit, keeping a "
                         "reply only when it is strictly closer. Only a candidate that compiles "
                         f"to the original body length with <= {repair.MAX_DIFF_WORDS} differing "
                         "words is repairable (a length difference is a different shape, not an "
                         "edit). Without --entry it selects the bank closest-first")
    ap.add_argument("--repair-rounds", type=int, default=4, metavar="N",
                    help="repair mode: maximum minimal-edit rounds per entry (default 4); the "
                         "loop also stops on a match, an ineligible candidate, or an "
                         "UNREACHABLE reply")
    ap.add_argument("--force", action="store_true",
                    help="process entries whose source already exists (overwrites)")
    ap.add_argument("--no-skip-existing", dest="skip_existing", action="store_false",
                    help="do not skip entries whose source exists (implies --force risk)")
    ap.add_argument("--rebuild", action="store_true", help="regenerate the bundle (Ghidra)")
    ap.add_argument("--dry-run", action="store_true",
                    help="select, bundle and print the prompt; do not call the model")
    args = ap.parse_args(argv)

    if args.entry and args.from_bank:
        print("error: --from-bank selects its own targets; drop --entry", file=sys.stderr)
        return 2

    layout = Layout(ledger=args.ledger, inventory=args.inventory, nso=args.nso,
                    context=args.context, src_root=args.src_root, work=args.work,
                    model_config=args.model_config, toolchain=args.toolchain)

    if not layout.ledger.exists():
        print(f"error: missing ledger {layout.ledger}", file=sys.stderr)
        return 2
    entries = read_entries(layout.ledger)
    # One reference ``.text`` read serves both the easy-first ordering and the template pass.
    reference = complexity.load_text(layout.nso)

    if args.repair:
        # Repair works off the bank, so it selects the bank closest-first unless a single
        # entry was named. The default divergence cap matches the repair budget.
        if not args.entry:
            args.from_bank = True
            if args.bank_max_divergences is None:
                args.bank_max_divergences = repair.MAX_DIFF_WORDS * 4
        args.repair_seeds = bank_seeds(layout)
        if not args.repair_seeds:
            print("error: --repair found no comparable banked candidates "
                  f"({bank_path(layout)}); run a normal pass first so there is a near miss to "
                  "repair", file=sys.stderr)
            return 1

    # One explicit target, or the next N pending entries.
    targets: list[dict] = []
    done: set[tuple[str, str]] = set()
    attempted: dict[tuple[str, str], int] | None = None
    if args.entry:
        try:
            targets = [resolve_entry(entries, args.module, args.entry)]
        except bundle.BundleError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    else:
        key = complexity_key(layout, reference) if args.order == "easiest" else None
        tier_key = complexity_key(layout, reference) if args.max_tier is not None else None
        if args.max_tier is not None and tier_key is None:
            print("error: --max-tier needs the reference .text (baserom/main.nso)",
                  file=sys.stderr)
            return 2
        attempted = attempted_counts(layout) if args.skip_attempted is not None else None
        bank = bank_priorities(layout) if args.from_bank else None
        if args.from_bank and not bank:
            print("error: --from-bank found no comparable near misses ",
                  f"({bank_path(layout)})", file=sys.stderr)
            return 1
        matchable = matchable_filter(layout, reference) if args.matchable else None
        for _ in range(max(1, args.limit)):
            nxt = select_next(entries, layout, skip_existing=args.skip_existing, done=done,
                              key=key, attempted=attempted,
                              skip_attempted=args.skip_attempted,
                              bank=bank,
                              bank_max_len_delta=args.bank_max_len_delta,
                              bank_max_divergences=args.bank_max_divergences,
                              tier_key=tier_key, max_tier=args.max_tier,
                              matchable=matchable)
            if nxt is None:
                break
            done.add(entry_key(nxt))
            targets.append(nxt)
        if args.skip_attempted is not None and len(targets) < max(1, args.limit):
            print(f"note: only {len(targets)} entr{'y' if len(targets) == 1 else 'ies'} "
                  f"selected; the rest are matched, already have a source, or drew "
                  f"{args.skip_attempted}+ attempts (lower --skip-attempted to revisit them)",
                  file=sys.stderr)
        if args.from_bank and len(targets) < max(1, args.limit):
            print(f"note: only {len(targets)} banked entr{'y' if len(targets) == 1 else 'ies'} "
                  f"matched the selection; raise --bank-max-len-delta/"
                  f"--bank-max-divergences to widen the pool", file=sys.stderr)
        if (args.max_tier is not None and len(targets) < max(1, args.limit)):
            print(f"note: only {len(targets)} entr{'y' if len(targets) == 1 else 'ies'} "
                  f"at tier <= {args.max_tier}; the tier is a difficulty ranking — try "
                  f"--matchable for 'what the gate can verify'", file=sys.stderr)
        if args.matchable and len(targets) < max(1, args.limit):
            print(f"note: only {len(targets)} matchable entr{'y' if len(targets) == 1 else 'ies'} "
                  f"selected; the rest read a literal pool or build a jump-table address, "
                  f"which needs the pool/GOT work (plan step 4)", file=sys.stderr)
    if not targets:
        print("error: no pending entries to process", file=sys.stderr)
        return 1

    model = None
    if not args.dry_run:
        try:
            model = model_client.from_config(
                layout.model_config, override_base_url=args.base_url,
                override_model=args.model_name, override_endpoint=args.endpoint,
                override_proxy=args.proxy, override_timeout=args.timeout,
                override_temperature=args.temperature,
                override_max_tokens=args.max_tokens,
                override_reasoning_effort=args.reasoning_effort, override_seed=args.seed)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"error: bad model config: {e}", file=sys.stderr)
            return 2

    matched = 0
    attempts_run = 0
    try:
        for entry in targets:
            outcome, used = attempt_entry(entry, entries, layout, args, model,
                                          one=process_repair if args.repair else process,
                                          raw_text=reference)
            attempts_run += used
            matched += outcome == "match"
    except KeyboardInterrupt:
        print(f"\ninterrupted: {attempts_run} attempt(s), {matched} match(es)",
              file=sys.stderr)
        return 130

    if args.dry_run:
        print(f"dry-run: {len(targets)} entry(ies) previewed")
        return 0
    print(f"done: {attempts_run} attempt(s), {matched} match(es)")
    return 0


@contextlib.contextmanager
def heartbeat(label: str, interval_s: float = 15.0):
    """Print a periodic "still running" line on stderr while a blocking call is in flight.

    A model call can take minutes (a cold load, or a long reasoning trace), so a silent wait is
    indistinguishable from a hang. A daemon thread prints an elapsed-time line every
    ``interval_s`` and is stopped when the block exits, including on an exception.
    """
    stop = threading.Event()

    def beat() -> None:
        waited = 0.0
        while not stop.wait(interval_s):
            waited += interval_s
            print(f"    \u2026 {label} still running ({waited:.0f}s)",
                  file=sys.stderr, flush=True)

    thread = threading.Thread(target=beat, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join()


def build_bundle_text(layout: Layout, entry: dict, args, body: int) -> str:
    """The context bundle for ``entry`` (reused unless ``--rebuild``; one Ghidra import)."""
    md = context_path(layout, entry)
    if args.rebuild or not md.exists():
        rc, out = run_subprocess(bundle_argv(layout, entry, body))
        if rc != 0:
            raise bundle.BundleError(f"bundle failed:\n{out.strip()[-800:]}")
    return md.read_text()


def ask_model(entry: dict, layout: Layout, args, model, body: int,
              feedback: "Feedback | None" = None):
    """Bundle, prompt, and call the model.

    Returns ``(candidate, completion, prompt, bundle_text)`` — the bundle text comes back
    with the prompt so the attempt record can fingerprint the retrieval output separately
    from the retry feedback that changes the prompt around it.
    """
    bundle_text = build_bundle_text(layout, entry, args, body)
    prompt = build_prompt(entry, bundle_text, feedback)
    print(f"    asking {getattr(model, 'model', 'model')} …", file=sys.stderr, flush=True)
    with heartbeat(entry["name"]):
        completion = model.complete(prompt, system=SYSTEM)
    print(f"    reply in {completion.latency_s:.0f}s ({completion.completion_tokens} tok)",
          file=sys.stderr, flush=True)
    return model_client.strip_fences(completion.text), completion, prompt, bundle_text


def gate_body(raw_body: bytes | None, body: int, partition: int) -> int:
    """The validated instruction-plus-pool extent to assert to the gate.

    The inventory's body is the instruction span. Reference literal-load targets extend it
    through alignment bytes and every pool word, without using the candidate's length.
    Missing reference bytes or invalid targets are errors, never a partition fallback.
    """
    if raw_body is None or len(raw_body) != body:
        raise ValueError("reference instruction bytes are unavailable for the gate extent")
    return complexity.function_extent(raw_body, partition)


def write_and_gate(entry: dict, layout: Layout, body: int | None, draft: Path,
                   candidate: str):
    """Write the candidate to its source path and run the byte gate.

    Returns ``(outcome, report, rc, gate_out)``. The report's presence is the source of truth:
    the gate writes it only after a successful compare, so no report means the candidate did
    not compile (rc 3) or the gate errored.
    """
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(candidate)
    report_path = layout.work / "bytegate" / f"{entry['module']}_{entry['addr']}.report.json"
    report_path.unlink(missing_ok=True)
    rc, gate_out = run_subprocess(gate_argv(layout, entry, body, report_path))
    report = json.loads(report_path.read_text()) if report_path.exists() else None
    outcome = ("match" if report["ok"] else "mismatch") if report is not None else "error"
    return outcome, report, rc, gate_out


def truncated(completion, model) -> bool:
    """Did the model spend its whole output budget before the answer began?

    ``finish_reason == "length"`` is the canonical signal (``"max_tokens"`` from providers that
    spell it that way); the completion-token count reaching the configured cap is the fallback
    for a server that omits the reason. An empty ``content`` plus this is a reasoning trace that
    never got to the answer, so resending the prompt only re-pays the same budget.
    """
    reason = (getattr(completion, "finish_reason", "") or "").lower()
    if reason in ("length", "max_tokens"):
        return True
    cap = getattr(model, "max_tokens", None)
    tokens = getattr(completion, "completion_tokens", None)
    return not reason and bool(cap) and tokens is not None and tokens >= cap


# --- the inline-assembly rule, enforced -------------------------------------------------
#
# The prompt forbids hand-written instructions: a translation unit must let the compiler pick
# every opcode. Exactly one construct spells `asm` without being hand-written code, and it is
# allowed:
#
#   * a symbol binding `... f(void) asm("mangled.name");`, which names the object symbol and
#     emits nothing.
#
# There is deliberately **no** allowance for the empty scheduling barrier
# `asm volatile("" ::: "memory")`. It does emit no instructions, but it was being used to make
# clang 4.0.1 reproduce branches the reference compiler kept and 4.0.1 if-converts (the `bxhi lr`
# guard class). Those matches were real bytes but not reconstructions: the source contained a
# construct the project bans, and the technique has been removed (see AGENTS.md, "The
# inline-assembly rule"). Any other asm is rejected before it reaches the gate, so "no inline
# asm" is a checked rule rather than a guideline the model can quietly ignore.

_ASM_CALL = re.compile(r"\b(?:__asm__|asm)\b\s*(?:volatile\s*|__volatile__\s*)?\(")
_SYMBOL_BINDING = re.compile(r'^\s*"[^"]*"\s*$')


def _brace_depth(src: str, index: int) -> int:
    """The ``{``-depth before ``index``, ignoring braces inside string literals."""
    depth, in_string, escaped = 0, False, False
    for ch in src[:index]:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
    return depth


def _prev_significant(src: str, index: int) -> str:
    """The last non-space character before ``index`` ('' at the start)."""
    j = index - 1
    while j >= 0 and src[j].isspace():
        j -= 1
    return src[j] if j >= 0 else ""


def asm_violation(src: str) -> str | None:
    """The first disallowed ``asm`` construct in a candidate, or ``None`` when it is clean.

    Allowed: a symbol binding at file scope attached to a declarator (``void f(void)
    asm("name");``). Everything else — the empty barrier ``asm volatile("" ::: "memory")``,
    instruction strings such as ``asm("nop")``, or a top-level ``asm("...")`` statement — is a
    violation.
    """
    for match in _ASM_CALL.finditer(src):
        depth, i = 1, match.end()
        while i < len(src) and depth:
            depth += {"(": 1, ")": -1}.get(src[i], 0)
            i += 1
        inner = src[match.end():i - 1]
        if (_SYMBOL_BINDING.match(inner)
                and _brace_depth(src, match.start()) == 0
                and (_prev_significant(src, match.start()).isalnum()
                     or _prev_significant(src, match.start()) == ")")):
            continue
        return (match.group(0) + inner + ")").strip()
    return None


def process(entry: dict, entries: list[dict], layout: Layout, args, model,
            raw_text: bytes | None = None, feedback: "Feedback | None" = None) -> str:
    """One loop iteration. Returns 'match' | 'mismatch' | 'error' | 'truncated' | 'dry-run'.

    A deterministic **template** (``tools/ledger/templates.py``) is tried first: it needs
    neither the context bundle nor the model, so a structural leaf skips both. The gate still
    decides; on a template miss the model is asked as a fallback, so this never regresses.

    ``feedback`` (a retry only) is the previous attempt's divergence, passed into the prompt so a
    retry edits rather than resamples; it is recorded (``feedback_used``) for auditability.

    An empty reply is ``error``; an empty reply that hit the output cap (see
    :func:`truncated`) is ``truncated``, meaning the model spent the whole ``max_tokens`` budget
    (a reasoning model can do this before emitting any answer) — retrying it is pure cost, so
    the caller stops.
    """
    module, addr, name = entry["module"], entry["addr"], entry["name"]
    body, extent_source = resolve_body(layout, entry, args.body)

    draft = ensure_under(safe_draft_path(entry, layout.src_root), layout.src_root)
    if draft.exists() and not args.force:
        raise ValueError(f"{draft} exists (use --force to overwrite)")

    # 1. template (no bundle, no model) — propose; the gate disposes.
    raw_body = complexity.body_of(raw_text, addr, body) if raw_text is not None else None
    hit = templates.propose_rule(raw_body, name) if raw_body is not None else None
    candidate = hit[2] if hit else None
    source = "template" if candidate is not None else "model"

    if args.dry_run:
        if hit is not None:
            print(f"--- template for {name} (rule #{hit[0]}: {hit[1]}, "
                  f"{body} B, {extent_source}) ---")
            print(candidate)
        else:
            print(f"--- prompt for {name} ({body} B, {extent_source}) ---")
            print(build_prompt(entry, build_bundle_text(layout, entry, args, body), feedback))
        return "dry-run"

    # 2. model — only when no template fired.
    completion = prompt = bundle_text = None
    if candidate is None:
        candidate, completion, prompt, bundle_text = ask_model(entry, layout, args, model,
                                                               body, feedback)
        if not candidate.strip():
            print(f"{name}: empty candidate from the model "
                  f"(finish_reason={completion.finish_reason or '?'}, "
                  f"{completion.completion_tokens} completion tok "
                  f"({completion.reasoning_tokens or 0} reasoning), "
                  f"{len(completion.reasoning)} chars of reasoning)")
            if truncated(completion, model):
                return "truncated"
            return "error"

    # 2b. the inline-assembly rule is checked, not trusted: hand-written instructions cannot
    #     match compiled C++, so such a candidate is never written or gated.
    bad_asm = asm_violation(candidate)
    if bad_asm is not None:
        print(f"{name}: rejected candidate — disallowed inline assembly "
              f"({bad_asm[:120]}); only a declarator symbol binding "
              '(`void f(void) asm("name");`) is permitted')
        return "error"

    # 3. write and verify (the gate is the only writer of verify=match).
    assert_body = gate_body(raw_body, body, int(entry["size"]))
    outcome, report, rc, gate_out = write_and_gate(entry, layout, assert_body, draft, candidate)

    # 4. a template that missed falls through to the model, so the path never regresses.
    if outcome != "match" and source == "template":
        candidate2, completion2, prompt2, bundle2 = ask_model(entry, layout, args, model,
                                                              body, feedback)
        if candidate2.strip() and asm_violation(candidate2) is None:
            candidate, source = candidate2, "model"
            hit = None                     # the rule missed; this is a model attempt now
            completion, prompt = completion2, prompt2
            bundle_text = bundle2
            outcome, report, rc, gate_out = write_and_gate(entry, layout, assert_body, draft,
                                                            candidate)

    # 5. record the attempt (append-only, parent-linked) — every attempt is kept.
    record = {
        "module": module, "addr": addr, "name": name, "body": body,
        "extent_source": extent_source, "outcome": outcome, "gate_rc": rc, "source": source,
        "kind": "retry" if feedback is not None else "plain",
        "model": completion.model if completion else "template",
        "prompt_tokens": completion.prompt_tokens if completion else None,
        "completion_tokens": completion.completion_tokens if completion else None,
        "reasoning_tokens": completion.reasoning_tokens if completion else None,
        "latency_s": completion.latency_s if completion else 0.0,
        "prompt_sha256": prompt_fingerprint(prompt or ""),
        "bundle_sha256": (prompt_fingerprint(bundle_text)
                          if bundle_text is not None else None),
        "toolchain_sha256": file_sha256(layout.toolchain),
        "gate_output": gate_out.strip()[-4000:],
    }
    if completion is not None:
        record.update(completion_fields(model, completion.prompt_tokens,
                                        completion.completion_tokens,
                                        completion.finish_reason,
                                        completion.system_fingerprint))
    if feedback is not None:
        record["feedback_used"] = True
    if hit is not None:
        record["template_rule"] = {"n": hit[0], "name": hit[1]}
    if report is not None:
        record["gate_status"] = report["status"]
        record["diff_count"] = report["diff_count"]
        record["diff_words"] = report.get("diff_words", [])
        record["gate"] = report.get("gate")
        record["gate_version"] = report.get("gate_version")
    stored = attempts.append(attempt_store(layout), record, candidate_text=candidate)

    # 6. bank a near miss (strictly-improving), and keep src/ matched-only.
    if outcome == "match":
        stamp = f"template rule #{hit[0]}: {hit[1]}" if hit else source
        print(f">>> MATCH  {name}  ({stamp})  -> {draft}  (attempt {stored['id']})")
    else:
        if report is not None:
            dist = nearmiss.closeness(report["diff_count"], report["cand_len"],
                                      report["ref_len"])
            pin = nearmiss.eval_pin(layout.toolchain)
            result = nearmiss.record(bank_path(layout), module, addr, dist, pin,
                                     name=name, attempt_id=stored["id"],
                                     gate_status=report["status"])
            if result.get("warn"):
                print(f"  warning: {result['warn']}", file=sys.stderr)
            note = (f"closeness={dist} ({result['reason']})" if result["updated"]
                    else f"closeness={dist} (kept {result['previous']})")
        else:
            note = f"no gate report (rc={rc})"
        if group_is_single(entries, module, entry["group"]):
            draft.unlink(missing_ok=True)
        else:
            print(f"  note: {entry['group']} is a merged TU; leaving {draft} in place")
        print(f"    {outcome.upper()}  {name}  attempt {stored['id']}  {note}")
    return outcome


def cleanup_repair_draft(entry: dict, entries: list[dict], draft: Path,
                         keep_source: str | None = None) -> None:
    """Leave ``src/`` matched-only after a repair session that did not match.

    A single-function translation unit is removed; a merged one must stay, so the *best*
    candidate (``keep_source``) is written back rather than whatever the last round produced.
    """
    if group_is_single(entries, entry["module"], entry["group"]):
        draft.unlink(missing_ok=True)
        return
    if keep_source:
        draft.write_text(keep_source)
    print(f"  note: {entry['group']} is a merged TU; leaving {draft} in place")


def process_repair(entry: dict, entries: list[dict], layout: Layout, args, model,
                   raw_text: bytes | None = None, feedback: "Feedback | None" = None) -> str:
    """One loop iteration in **repair mode** (``--repair``): iterate on a banked near miss.

    Instead of asking for a fresh translation unit, this seeds the loop with the entry's best
    banked candidate and hands it to :func:`repair.repair`, which asks the model for a *minimal
    edit* of that exact unit and keeps a reply only when the gate says it is strictly closer
    (``|cand_len - ref_len|``, then ``diff_count``). The gate remains the only writer of
    ``verify=match``; every gated candidate is still appended to the attempt log and (when it
    misses) folded into the bank, so a repair session is as auditable as a normal attempt.

    ``feedback`` is accepted only to satisfy the ``one`` protocol of :func:`attempt_entry` —
    repair threads its own divergence, so a run-level retry must not double it.

    The draft is left in ``src/`` only on a match (the near-miss rule: matched code only).
    """
    module, addr, name = entry["module"], entry["addr"], entry["name"]
    body, extent_source = resolve_body(layout, entry, args.body)

    draft = ensure_under(safe_draft_path(entry, layout.src_root), layout.src_root)
    if draft.exists() and not args.force:
        raise ValueError(f"{draft} exists (use --force to overwrite)")

    seeds = getattr(args, "repair_seeds", None)
    seed = seeds.get((module, addr)) if seeds else None
    if seed is None:
        seed = bank_seed(layout, module, addr)
    if seed is None:
        print(f"    repair: {name} has no banked candidate to repair")
        return "error"
    seed_source, seed_id = seed

    bundle_text = build_bundle_text(layout, entry, args, body)
    raw_body = complexity.body_of(raw_text, addr, body) if raw_text is not None else None
    assert_body = gate_body(raw_body, body, int(entry["size"]))
    if args.dry_run:
        print(f"--- repair prompt for {name} ({body} B, {extent_source}; "
              f"seed attempt {seed_id}) ---")
        print(repair_prompt(entry, bundle_text, seed_source, None, ""))
        return "dry-run"

    meta: dict = {}

    def gate(source: str):
        """Compile + byte-compare one candidate, recording it like a normal attempt."""
        bad_asm = asm_violation(source)
        if bad_asm is not None:
            print(f"{name}: rejected candidate — disallowed inline assembly "
                  f"({bad_asm[:120]}); only a declarator symbol binding "
                  '(`void f(void) asm("name");`) is permitted')
            return None, "rejected: disallowed inline assembly"
        outcome, report, rc, gate_out = write_and_gate(entry, layout, assert_body, draft,
                                                       source)
        record = {
            "module": module, "addr": addr, "name": name, "body": body,
            "extent_source": extent_source, "outcome": outcome, "gate_rc": rc,
            "source": "repair", "kind": "repair", "repair_seed": seed_id,
            "model": meta.get("model", "seed"),
            "prompt_tokens": meta.get("prompt_tokens"),
            "completion_tokens": meta.get("completion_tokens"),
            "reasoning_tokens": meta.get("reasoning_tokens"),
            "latency_s": meta.get("latency_s", 0.0),
            "prompt_sha256": prompt_fingerprint(meta.get("prompt", "")),
            "bundle_sha256": prompt_fingerprint(bundle_text),
            "toolchain_sha256": file_sha256(layout.toolchain),
            "gate_output": gate_out.strip()[-4000:],
        }
        record.update(completion_fields(model, meta.get("prompt_tokens"),
                                        meta.get("completion_tokens"),
                                        meta.get("finish_reason") or "",
                                        meta.get("system_fingerprint") or ""))
        if report is not None:
            record["gate_status"] = report["status"]
            record["diff_count"] = report["diff_count"]
            record["diff_words"] = report.get("diff_words", [])
            record["gate"] = report.get("gate")
            record["gate_version"] = report.get("gate_version")
        stored = attempts.append(attempt_store(layout), record, candidate_text=source)
        if report is not None and outcome != "match":
            try:
                pin = nearmiss.eval_pin(layout.toolchain)
                nearmiss.record(bank_path(layout), module, addr,
                                nearmiss.closeness(report["diff_count"],
                                                   report["cand_len"], body),
                                pin, name=name, attempt_id=stored["id"],
                                gate_status=report["status"])
            except ValueError:
                pass
        return report, gate_out

    def ask(prompt: str) -> str:
        print(f"    asking {getattr(model, 'model', 'model')} …", file=sys.stderr, flush=True)
        with heartbeat(name):
            completion = model.complete(prompt, system=SYSTEM)
        print(f"    reply in {completion.latency_s:.0f}s "
              f"({completion.completion_tokens} tok)", file=sys.stderr, flush=True)
        meta.update(model=completion.model, prompt_tokens=completion.prompt_tokens,
                    completion_tokens=completion.completion_tokens,
                    reasoning_tokens=completion.reasoning_tokens,
                    latency_s=completion.latency_s, prompt=prompt,
                    finish_reason=completion.finish_reason or None,
                    system_fingerprint=completion.system_fingerprint or None)
        return model_client.strip_fences(completion.text)

    try:
        result = repair.repair(
            seed_source, gate=gate, ask=ask,
            prompt_for=lambda source, report, out: repair_prompt(entry, bundle_text, source,
                                                                 report, out),
            rounds=getattr(args, "repair_rounds", 4),
            log=lambda msg: print(msg, file=sys.stderr))
    except BaseException:
        # A transport error mid-session must not leave an unmatched draft in src/ (that tree
        # holds matched code only), nor a stale source that would hide the entry from selection.
        cleanup_repair_draft(entry, entries, draft)
        raise

    if result.matched:
        print(f">>> MATCH  {name}  (repair, {result.rounds_used} round(s))  -> {draft}")
        return "match"
    cleanup_repair_draft(entry, entries, draft, result.source)
    note = (f"closeness={list(repair.closeness(result.report))}" if result.report is not None
            else "no gate report")
    print(f"    {result.outcome.upper()}  {name}  repair stopped after "
          f"{result.rounds_used} round(s)  {note}")
    return result.outcome


def attempt_entry(entry: dict, entries: list[dict], layout: Layout, args, model,
                  one=process, raw_text: bytes | None = None) -> tuple[str, int]:
    """Run one entry up to ``args.attempts`` times, stopping on a match.

    Returns ``(outcome, attempts_used)``. Every attempt is recorded (parent-linked) by
    ``process``; a transport or bundle error counts as an attempt and is retried, since a
    runaway generation or a cold-load timeout is often transient. ``--dry-run`` previews once.

    Between attempts the previous attempt's divergence is threaded back in as ``feedback`` so a
    retry revises the last candidate instead of resampling an identical prompt (disable with
    ``--no-feedback``). Retrying also stops early once a mismatch reproduces the *same*
    divergence as the attempt before it — the feedback moved nothing, so further tries are waste.

    A candidate that does not compile is a *distinct* failure mode from a near miss, so it is
    counted against its own, usually smaller budget (``--compile-attempts``): once this many
    attempts were rejected by clang, the entry is abandoned instead of burning every match
    attempt on code that never gets as far as the byte comparison.
    """
    outcome = "error"
    used = 0
    store = attempt_store(layout)
    feedback = None
    prev_words: list | None = None
    enabled = getattr(args, "feedback", True)
    compile_budget = max(0, getattr(args, "compile_attempts", 2))
    compile_failures = 0
    last_id = None
    for _ in range(max(1, args.attempts)):
        try:
            outcome = one(entry, entries, layout, args, model, raw_text, feedback)
        except (attempts.AttemptError, bundle.BundleError, model_client.ModelError,
                ValueError) as e:
            print(f"error: {entry['name']}: {e}", file=sys.stderr)
            outcome = "error"
        used += 1
        if outcome in ("match", "dry-run"):
            break
        if outcome == "truncated":
            print(f"    stop: {entry['name']} was cut off at max_tokens before emitting an "
                  f"answer; raise --max-tokens (or turn the model's reasoning off), not "
                  f"the attempt count", file=sys.stderr)
            outcome = "error"
            break
        try:
            record = attempts.latest_for(store / "log.jsonl", entry["module"], entry["addr"])
        except attempts.AttemptError:
            record = None
        # Only a *fresh* record is this attempt's own (an empty candidate or a raised exception
        # appends nothing, leaving the previous record in place, so it must not be recounted).
        # A compile failure is ``error`` with a gate exit of 3; it draws on its own budget.
        if record is not None and record.get("id") != last_id:
            last_id = record.get("id")
            if record.get("outcome") == "error" and record.get("gate_rc") == 3:
                compile_failures += 1
                if compile_failures >= compile_budget:
                    print(f"    stop: {entry['name']} hit the compile-failure budget "
                          f"({compile_failures}); the candidate never compiles", file=sys.stderr)
                    break
        if not enabled:
            continue
        feedback = feedback_from_record(record, store)
        words = feedback.diff_words if feedback else None
        if outcome == "mismatch" and words and words == prev_words:
            print(f"    stall: {entry['name']} repeated the same divergence; stopping early",
                  file=sys.stderr)
            break
        prev_words = words if words else prev_words
    return outcome, used


if __name__ == "__main__":
    raise SystemExit(main())
