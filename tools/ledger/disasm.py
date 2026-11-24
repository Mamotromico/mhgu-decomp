"""Decode A32 machine-code bytes for gate reports (PLAN.MD 3.1, aligned feedback).

The byte gate compares bytes; this decodes the *compared* bytes — both the patched candidate
and the reference extent — so a retry/repair prompt can show the model's own instruction
next to the original's instead of raw hex words it cannot read.

Decoder: devkitARM ``arm-none-eabi-objdump`` (GNU binutils 2.42) in raw-binary mode, with
``-M reg-names-std`` so register names match the bundle's ``r0``-``r15`` convention. That
build decodes the ARMv8-A FP/NEON encodings this image contains (``vselgt.f32`` and friends),
which the pinned ``llvm-objdump`` cannot: it byte-shifts ARM streams (see AGENTS.md). Ubuntu's
host objdump has no ARM target at all.

Everything here is **best-effort**: a missing tool or a decode failure yields
``{"available": false}`` — the gate's verdict never depends on this module.
"""

from __future__ import annotations

import functools
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

OBJDUMP = "arm-none-eabi-objdump"

# The disassembly-line shape: ``   0:	fe300a81 	vselgt.f32	s0, s1, s2`` (GNU prints the
# whole instruction word as one contiguous hex column).
_LINE = re.compile(r"^\s*([0-9a-f]+):\s+([0-9a-f]{2}(?:[0-9a-f]{2})*)\s+(\S+)(?:\s+(.*?))?\s*$")

# A literal-pool load: ``ldr r0, [pc, #20]`` / ``vldr s4, [pc, #12]`` (decimal or 0x).
_PC_LOAD = re.compile(r"\[pc\s*,\s*#(-?(?:0x)?[0-9a-f]+)\]", re.IGNORECASE)

# A32 condition codes; a branch mnemonic is ``b``/``bl`` plus one of these (``ble`` = b+le,
# ``bleq`` = bl+eq — the ``bl``+cond form is checked first).
_CONDS = ("eq", "ne", "cs", "cc", "mi", "pl", "vs", "vc",
          "hi", "ls", "ge", "lt", "gt", "le", "al")

BRANCH_LIST_LIMIT = 12


def find_objdump() -> str | None:
    """The devkitARM objdump on ``PATH``, or ``None`` (the loop then falls back)."""
    return shutil.which(OBJDUMP)


@functools.lru_cache(maxsize=8)
def _tool_label(exe: str) -> str:
    """How to name the decoder in a report: its own version line."""
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True,
                             timeout=15).stdout
        return out.splitlines()[0].strip() if out.strip() else Path(exe).name
    except (OSError, subprocess.SubprocessError):
        return Path(exe).name


def parse_objdump(text: str) -> dict[int, str]:
    """``offset -> "mnemonic operands"`` from GNU objdump's flat disassembly.

    Header/footer lines (``file format binary``, section banners) do not match and are
    skipped. Raw-binary mode has no symbols, so operands carry no ``<f+0x..>`` annotations.
    """
    out: dict[int, str] = {}
    for line in text.splitlines():
        m = _LINE.match(line)
        if not m:
            continue
        mnemonic = m.group(3)
        if mnemonic is None:
            continue
        out[int(m.group(1), 16)] = (mnemonic + (" " + m.group(4) if m.group(4) else "")).strip()
    return out


def disassemble(buf: bytes, exe: str | None = None,
                runner=subprocess.run) -> dict[int, str] | None:
    """Decode a word-aligned A32 buffer, or ``None`` when the tool is missing/failing.

    ``runner`` is injectable for tests: called as ``runner(argv)`` and expected to return a
    ``subprocess.CompletedProcess``-like object.
    """
    exe = exe or find_objdump()
    if exe is None or not buf:
        return None
    tmp = Path(tempfile.mkstemp(suffix=".bin", prefix="bytegate-")[1])
    try:
        tmp.write_bytes(buf)
        argv = [exe, "-b", "binary", "-m", "arm", "-M", "reg-names-std", "-D", str(tmp)]
        proc = runner(argv, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0 or not proc.stdout:
            return None
        return parse_objdump(proc.stdout)
    finally:
        tmp.unlink(missing_ok=True)


def classify(mnemonic: str) -> str | None:
    """A branch/call class for a mnemonic: ``cond-br``, ``br``, ``call``, or ``None``.

    ``bx``/``blx`` and plain computational mnemonics return ``None``. The ``bl``+cond check
    runs before ``b``+cond so ``bleq`` is a conditional call while ``ble`` is a conditional
    branch (b+le).
    """
    m = mnemonic.lower()
    if m in ("cbz", "cbnz"):
        return "cond-br"
    if m == "b":
        return "br"
    if m in ("bl", "blx"):
        return "call"
    if m.startswith("bl") and m[2:] in _CONDS:
        return "call"
    if m.startswith("b") and m[1:] in _CONDS:
        return "cond-br"
    return None


def _imm(text: str) -> int:
    return int(text, 16 if text.lower().startswith("0x") else 10)


def structure(lines: dict[int, str]) -> dict:
    """A compact body summary: counts and the branch list, with pool words excluded.

    First pass marks every word a PC-relative load points at (A32 ``pc`` reads as ``addr+8``)
    as a literal-pool word; those decode as garbage in raw mode and must not be counted as
    instructions. ``branches`` lists the conditional/unconditional branches as
    ``+0x<offset>  <text>``, capped at :data:`BRANCH_LIST_LIMIT` with a ``+N more`` tail.
    """
    pool: set[int] = set()
    pool_loads = 0
    for off, text in lines.items():
        m = _PC_LOAD.search(text)
        if m:
            pool_loads += 1
            target = off + 8 + _imm(m.group(1))
            if target in lines:
                pool.add(target)
    insns = cond_br = br = calls = 0
    branches: list[str] = []
    for off in sorted(lines):
        if off in pool:
            continue
        cls = classify(lines[off].split(None, 1)[0])
        if cls is None:
            insns += 1
            continue
        insns += 1
        if cls == "call":
            calls += 1
            continue
        if cls == "cond-br":
            cond_br += 1
        else:
            br += 1
        if len(branches) < BRANCH_LIST_LIMIT:
            branches.append(f"+0x{off:x}  {lines[off]}")
    remaining = cond_br + br - len(branches)
    if remaining > 0:
        branches.append(f"+{remaining} more")
    return {"insns": insns, "cond_br": cond_br, "br": br, "calls": calls,
            "pool_loads": pool_loads, "branches": branches, "pool_words": len(pool)}


def compare(cand: bytes, ref: bytes, sites) -> dict:
    """The decoded feedback block for a non-match report (never raises).

    ``sites`` are the diff offsets (the gate's ``diff_words``). Returns
    ``{"available": true, "tool", "sites": {offset: {"got", "want"}}, "cand", "ref"}`` where
    the two structure summaries decode each compared body; a missing objdump or a decode
    failure yields ``{"available": false, "reason"}`` and callers keep the legacy hex-only
    rendering.
    """
    try:
        exe = find_objdump()
        if exe is None:
            return {"available": False, "reason": f"{OBJDUMP} not on PATH"}
        cand_lines = disassemble(cand, exe=exe) or {}
        ref_lines = disassemble(ref, exe=exe) or {}
        site_map: dict[str, dict] = {}
        for off in sites:
            got, want = cand_lines.get(off), ref_lines.get(off)
            if got is not None or want is not None:
                site_map[str(off)] = {"got": got, "want": want}
        return {"available": True, "tool": _tool_label(exe), "sites": site_map,
                "cand": structure(cand_lines), "ref": structure(ref_lines)}
    except Exception as e:  # best-effort decoration must never fail the gate
        return {"available": False, "reason": f"{type(e).__name__}: {e}"}
