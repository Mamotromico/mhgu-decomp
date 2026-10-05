"""The context bundle: the model's entire view of one function, generated deterministically.

A *bundle* is everything the local model is shown for one ledger entry — the annotated
disassembly of the original, the original's own bytes, and the call targets it names. It is
**disassembly-first and annotated** (``docs/llm-harness-design.md`` → *The context bundle*):
a ``bl``/``blx`` names its callee, every branch names its target, and a pc-relative literal-pool
load shows the value it loads — raw mnemonics alone are not enough to reconstruct the compiler's
idioms.

Two properties are non-negotiable and shape the code:

* **Deterministic and one-way.** The generator only *reads* the binary, the ledger and the
  inventory, and only *writes* under the git-ignored ``baserom/work/context/``. It never edits
  the ledger or ``src/``.
* **Body extent, not partition.** The ledger's ``size`` is a block *partition* (distance to the
  next cut point) and over-covers a function whose trailing region was never cut
  (``func_601a72e4``: a 60 B body in a 1368 B partition). The bundle disassembles and slices the
  **body**, resolved from the full-analysis inventory (``inventory.tsv``, whose function ``size``
  is the real body and matches the PoC probes exactly) or an explicit ``--body``.

The Ghidra draft decompiler is deliberately **absent** — the schema has no draft field, so the
harness cannot be tempted to pass one (see the design doc → *the Ghidra decompiler draft is
excluded from the LLM context*).

The heavy, impure step (a Ghidra headless run that dumps the memory blocks and disassembles the
body range) is isolated in ``run_ghidra``; everything else — extent resolution, disassembly
parsing, annotation, rendering — is pure and unit-tested in ``tests/loop/test_bundle.py``.

Usage::

    python3 tools/loop/bundle.py main 601a72e4
    python3 tools/loop/bundle.py main 601a72e4 --body 60 --print
    python3 tools/loop/bundle.py --next            # bundle the next pending entry
    python3 tools/loop/bundle.py main 601a72e4 --asm FILE --ref-dir DIR   # skip Ghidra
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))
sys.path.insert(0, str(REPO / "tools" / "loop"))

from ledgerlib import read_entries  # noqa: E402
import worklist  # noqa: E402

DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_INVENTORY = REPO / "baserom" / "work" / "inventory" / "inventory.tsv"
DEFAULT_NSO = REPO / "baserom" / "main.nso"
DEFAULT_OUT = REPO / "baserom" / "work" / "context"
GHIDRA_HOME = os.environ.get("GHIDRA_HOME", "/opt/ghidra")


class BundleError(Exception):
    """A bundle could not be produced (missing extent, no Ghidra, bad input)."""


# --- pure helpers (unit-tested) -------------------------------------------------------

def parse_inventory(text: str) -> dict[str, int]:
    """Map ``addr -> body size`` for the ``function`` rows of an ``inventory.tsv``.

    The inventory is the full-analysis export; its ``size`` is the real function body (not
    the ledger partition). Only ``function`` rows are kept.
    """
    sizes: dict[str, int] = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 3 or fields[1] != "function":
            continue
        try:
            sizes[fields[0]] = int(fields[2])
        except ValueError:
            continue
    return sizes


def resolve_body(entry: dict, sizes: dict[str, int], override: int | None = None) -> tuple[int, str]:
    """The body length and where it came from: ``("override"|"inventory", n)``.

    Raises ``BundleError`` when neither source has it — the generator never falls back to
    the partition (the very bug this module exists to avoid).
    """
    if override is not None:
        if override <= 0:
            raise BundleError(f"--body must be positive, got {override}")
        return override, "override"
    size = sizes.get(entry["addr"])
    if size is None or size <= 0:
        raise BundleError(
            f"no body extent for {entry['name']} ({entry['addr']}): it is not in the "
            f"inventory and no --body was given. Run tools/ghidra/inventory.sh, or pass "
            f"--body N (see poc/probes.tsv).")
    return size, "inventory"


def name_table(entries: list[dict], module: str) -> dict[str, str]:
    """``addr -> ledger name`` for one module's addressed entries (the naming authority)."""
    return {e["addr"]: e["name"] for e in entries
            if e["module"] == module and e["addr"]}


def target_name(addr: str, names: dict[str, str]) -> str:
    """The ledger name for an address, or a synthetic ``loc_<addr>`` label."""
    return names.get(addr) or f"loc_{addr}"


def parse_disasm(text: str) -> list[dict]:
    """Parse ``AnnotateFunctions`` TSV into instruction dicts.

    Rows are ``addr, bytes, mnemonic, operands, flows`` (tab-separated). Short or malformed
    rows are skipped rather than raising, so one bad line cannot sink a bundle.
    """
    insns: list[dict] = []
    for line in text.splitlines():
        if not line or line.startswith(";;") or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 5:
            continue
        insns.append({
            "addr": fields[0],
            "bytes": fields[1],
            "mnemonic": fields[2],
            "operands": fields[3],
            "flows": [a for a in fields[4].split(",") if a],
        })
    return insns


# An absolute memory operand, e.g. the resolved target of a pc-relative load:
#   ldr r0, [0x60001058]      -> 0x60001058
# Register-based forms ([r0,#4], [pc,r0]) carry no constant and are not matched.
_ABS_OPERAND = re.compile(r"\[(0x[0-9a-fA-F]+)\]")


def literal_slots(operands: str) -> list[int]:
    """Absolute memory operand addresses in an operand string (as ints)."""
    return [int(m, 16) for m in _ABS_OPERAND.findall(operands)]


def annotate(insns: list[dict], names: dict[str, str], read_word) -> list[dict]:
    """Resolve branch-target names and literal-pool values; return new instruction dicts.

    ``read_word(addr:int) -> int | None`` supplies the binary word at a literal slot (the
    caller wires it to the dumped memory blocks; tests inject a stub). Each literal whose word
    is itself a known address also gains a ``name``.
    """
    out: list[dict] = []
    for ins in insns:
        rec = dict(ins)
        rec["flow_names"] = [target_name(a, names) for a in ins["flows"]]
        literals = []
        for slot in literal_slots(ins["operands"]):
            value = read_word(slot)
            if value is None:
                continue
            lit = {"slot": f"{slot:08x}", "value": value}
            pointed = names.get(f"{value:08x}")
            if pointed:
                lit["name"] = pointed
            literals.append(lit)
        rec["literals"] = literals
        out.append(rec)
    return out


def callees(insns: list[dict], names: dict[str, str]) -> list[tuple[str, str]]:
    """Distinct ``(addr, name)`` call targets, in first-seen order (``bl``/``blx`` only)."""
    seen: dict[str, str] = {}
    for ins in insns:
        if not ins["mnemonic"].startswith("bl"):
            continue
        for addr in ins["flows"]:
            seen.setdefault(addr, target_name(addr, names))
    return list(seen.items())


def hex_words(data: bytes) -> str:
    """Group bytes into 4-byte little-endian words as space-separated hex (as seen in a dump)."""
    return " ".join(data[i:i + 4].hex() for i in range(0, len(data), 4))


def format_insn(ins: dict) -> str:
    """One disassembly line, with resolved flow and literal notes appended."""
    text = f"    {ins['addr']}  {ins['bytes']:<8}  {ins['mnemonic']:<7} {ins['operands']}"
    notes = [f"-> {name}" for name in ins.get("flow_names", [])]
    for lit in ins.get("literals", []):
        note = f"= 0x{lit['value']:08x}"
        if lit.get("name"):
            note += f" ({lit['name']})"
        notes.append(note)
    return (text.rstrip() + ("  ; " + ", ".join(notes) if notes else "")).rstrip()


def render(meta: dict, insns: list[dict]) -> str:
    """The deterministic bundle text (the model's whole view of the function)."""
    lines = [
        f"# bundle: {meta['name']}",
        "",
        f"module    {meta['module']}",
        f"address   {meta['addr']}",
        f"block     {meta['block']}",
        f"group     {meta['group']}",
        f"kind      {meta['kind']}",
        f"body      {meta['body']} B  (source: {meta['extent_source']})",
        f"partition {meta['partition']} B  (ledger; the body is authoritative)",
        "",
        f"## original bytes ({meta['body']} B)",
        "",
        f"    {meta['body_hex']}",
        "",
        "## disassembly",
        "",
    ]
    lines.extend(format_insn(ins) for ins in insns)
    lines += ["", "## calls", ""]
    if meta["callees"]:
        lines += [f"    {addr}  {name}" for addr, name in meta["callees"]]
    else:
        lines.append("    (none)")
    lines.append("")
    return "\n".join(lines)


# --- memory blocks from the Ghidra dump -----------------------------------------------

class Blocks:
    """The dumped memory blocks (``<block>_<startHex>.bin``), addressable by absolute address."""

    def __init__(self, ref_dir: Path):
        self.segments: list[tuple[int, bytes]] = []
        for path in sorted(Path(ref_dir).glob("*.bin")):
            try:
                start = int(path.stem.rsplit("_", 1)[-1], 16)
            except ValueError:
                continue
            self.segments.append((start, path.read_bytes()))

    def _find(self, addr: int) -> tuple[int, bytes] | None:
        for start, data in self.segments:
            if start <= addr < start + len(data):
                return start, data
        return None

    def read_word(self, addr: int) -> int | None:
        found = self._find(addr)
        if found is None:
            return None
        start, data = found
        off = addr - start
        if off + 4 > len(data):
            return None
        return struct.unpack_from("<I", data, off)[0]

    def bytes_at(self, addr: int, length: int) -> bytes | None:
        found = self._find(addr)
        if found is None:
            return None
        start, data = found
        off = addr - start
        return data[off:off + length]


# --- the Ghidra backend (impure) ------------------------------------------------------

def run_ghidra(nso: Path, req_file: Path, asm_out: Path, ref_dir: Path, project_dir: Path,
               ghidra_home: str = GHIDRA_HOME) -> None:
    """Import the NSO into a throwaway project, dump blocks, and disassemble the request.

    One headless run does both post-scripts, so a bundle costs one import (the gate pays the
    same import via ``dump_blocks.sh``).
    """
    analyze = Path(ghidra_home) / "support" / "analyzeHeadless"
    if not analyze.exists():
        raise BundleError(f"Ghidra not found at {analyze} (set GHIDRA_HOME)")
    if not nso.exists():
        raise BundleError(f"NSO not found: {nso}")

    shutil.rmtree(project_dir, ignore_errors=True)
    project_dir.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(ref_dir, ignore_errors=True)
    ref_dir.mkdir(parents=True, exist_ok=True)
    asm_out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(analyze), str(project_dir), "soaratorium",
        "-import", str(nso), "-noanalysis",
        "-scriptPath", str(REPO / "tools" / "ghidra"),
        "-postScript", "DumpMemoryBlocks.java", str(ref_dir),
        "-postScript", "AnnotateFunctions.java", str(req_file), str(asm_out),
    ]
    log = project_dir.parent / "bundle.log"
    try:
        with log.open("w") as fh:
            result = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT)
        if result.returncode != 0 or not asm_out.exists():
            tail = log.read_text().splitlines()[-25:]
            raise BundleError(f"Ghidra run failed (see {log}):\n" + "\n".join(tail))
    finally:
        # The project is only a vehicle for this one import; keep nothing.
        shutil.rmtree(project_dir, ignore_errors=True)


# --- main -----------------------------------------------------------------------------

def find_entry(entries: list[dict], module: str, addr: str) -> dict:
    entry = next((e for e in entries if e["module"] == module and e["addr"] == addr), None)
    if entry is None:
        raise BundleError(f"no ledger entry ({module}, {addr})")
    if entry["kind"] != "function":
        raise BundleError(f"({module}, {addr}) is kind {entry['kind']!r}, not a function")
    return entry


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("module", nargs="?", help="ledger module (omit with --next)")
    ap.add_argument("addr", nargs="?", help="ledger address (omit with --next)")
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="bundle output dir (git-ignored)")
    ap.add_argument("--ref-dir", type=Path, default=None,
                    help="block dump dir (default <out>/<module>/<addr>.ref)")
    ap.add_argument("--body", type=int, default=None,
                    help="authoritative body length in bytes (overrides the inventory)")
    ap.add_argument("--next", action="store_true",
                    help="ignore positional args; bundle the next pending function")
    ap.add_argument("--skip-existing", action="store_true",
                    help="with --next, skip entries whose source already exists")
    ap.add_argument("--asm", type=Path, default=None,
                    help="precomputed AnnotateFunctions TSV; skips the Ghidra run")
    ap.add_argument("--print", dest="echo", action="store_true",
                    help="also print the bundle to stdout")
    ap.add_argument("--json", action="store_true", help="print a JSON record instead")
    args = ap.parse_args(argv)

    try:
        entries = read_entries(args.ledger)
    except OSError as e:
        print(f"error: cannot read ledger: {e}", file=sys.stderr)
        return 2

    if args.next:
        queue = worklist.select(entries)
        if args.skip_existing:
            src_root = REPO / worklist.source_root(REPO / "config" / "build.json")
            queue = [e for e in queue if not worklist.source_path(e, src_root).exists()]
        if not queue:
            print("error: worklist is empty", file=sys.stderr)
            return 1
        entry = queue[0]
        module, addr = entry["module"], entry["addr"]
    elif args.module and args.addr:
        module = args.module
        addr = args.addr.lower().removeprefix("0x").zfill(8)
        try:
            entry = find_entry(entries, module, addr)
        except BundleError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    else:
        ap.error("provide <module> <addr>, or --next")

    # 1. body extent — inventory (or --body); never the partition.
    sizes = (parse_inventory(args.inventory.read_text())
             if args.inventory.exists() else {})
    try:
        body, source = resolve_body(entry, sizes, args.body)
    except BundleError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    addr_int = int(entry["addr"], 16)
    out_dir = args.out / module
    ref_dir = args.ref_dir or (out_dir / f"{entry['addr']}.ref")

    # 2. reference blocks + annotated disassembly.
    if args.asm is not None:
        asm_text = args.asm.read_text()
    else:
        req = out_dir / f"{entry['addr']}.req"
        asm_out = out_dir / f"{entry['addr']}.asm.tsv"
        out_dir.mkdir(parents=True, exist_ok=True)
        req.write_text(f"{entry['addr']} {body}\n")
        try:
            run_ghidra(args.nso, req, asm_out, ref_dir, args.out / "_ghidra")
        except BundleError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        asm_text = asm_out.read_text()

    blocks = Blocks(ref_dir)
    body_bytes = blocks.bytes_at(addr_int, body)
    if body_bytes is None or len(body_bytes) != body:
        print(f"error: could not read {body} B at {entry['addr']} from {ref_dir} "
              f"(got {0 if body_bytes is None else len(body_bytes)})", file=sys.stderr)
        return 1

    names = name_table(entries, module)
    insns = annotate(parse_disasm(asm_text), names, blocks.read_word)

    meta = {
        "name": entry["name"], "module": module, "addr": entry["addr"],
        "block": entry["block"], "group": entry["group"], "kind": entry["kind"],
        "body": body, "extent_source": source, "partition": int(entry["size"]),
        "body_hex": hex_words(body_bytes),
        "callees": callees(insns, names),
    }

    bundle_path = out_dir / f"{entry['addr']}.md"
    bundle_path.write_text(render(meta, insns))
    print(f"bundle: {entry['name']}  {body} B ({source})  -> {bundle_path}")

    if args.json:
        print(json.dumps({"meta": meta, "instructions": insns}, indent=2))
    elif args.echo:
        print()
        print(render(meta, insns))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
