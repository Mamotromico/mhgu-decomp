"""Re-gate the candidates already stored by earlier loop runs against the current gate.

The attempt log (``baserom/work/attempts/log.jsonl``) records a verdict from *whatever
gate existed when the attempt ran*. The gate has since become relocation-aware, and the
compiler pin changed, so a stored ``MISMATCH`` is not evidence of an unmatchable function:
it may merely be a verdict from the old raw-byte gate (``AGENTS.md`` → *Note (gate)*).

This module turns that into matches at **zero model cost**: for a chosen set of entries it
copies each stored candidate into ``src/<module>/<group>.cpp``, runs the current gate, and
reports the conversions. It is measurement-only by default; ``--update`` writes the
``verify=match`` rows back through the gate's own ``--update`` path.

Usage::

    python3 tools/ledger/regate_candidates.py --limit 60
    python3 tools/ledger/regate_candidates.py --class plain --jobs 8 --tsv out.tsv
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))

import complexity  # noqa: E402

LOG = REPO / "baserom" / "work" / "attempts" / "log.jsonl"
ATTEMPTS = REPO / "baserom" / "work" / "attempts"
REF_DIR = REPO / "baserom" / "work" / "bytegate" / "ref"
GATE = REPO / "tools" / "ledger" / "bytegate.py"


def is_veneer(body: bytes | None) -> bool:
    """Re-exported from :mod:`complexity` so the sweep and the selector share one definition."""
    return complexity.is_veneer(body)


def has_cond_return(body: bytes | None) -> bool:
    """A conditional ``bxCC lr`` — the guard class no source shape restores (see AGENTS.md)."""
    if body is None:
        return False
    for off in range(0, len(body) - 3, 4):
        w = int.from_bytes(body[off:off + 4], "little")
        if (w & 0x0FFFFFFF) == 0x012FFF1E and ((w >> 28) & 0xF) not in (0xE, 0xF):
            return True
    return False


def classify(body: bytes | None) -> str:
    if body is None:
        return "unreadable"
    if is_veneer(body):
        return "veneer"
    if not complexity.gateable(body):
        return "ungateable"
    if has_cond_return(body):
        return "guard"
    return "plain"


def load_entries() -> dict[tuple[str, str], list[dict]]:
    by: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    with LOG.open() as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                by[(r["module"], r["addr"])].append(r)
    return by


def find_ref_bin() -> Path:
    hits = sorted(REF_DIR.glob(".text_*.bin"))
    if len(hits) != 1:
        raise SystemExit(f"expected one .text dump in {REF_DIR}, found {len(hits)}")
    return hits[0]


def gate_one(cand: Path, module: str, addr: str, size: int, ref_bin: Path,
             update: bool, keep_on_match: bool = False) -> dict:
    """Copy ``cand`` into the src tree and gate it; restore whatever was there.

    With ``keep_on_match`` a winning candidate is left in place as the entry's real source
    (otherwise the tree is restored, so the sweep is side-effect free).
    """
    group = f"func_{addr}"
    dst = REPO / "src" / module / f"{group}.cpp"
    backup = None
    if dst.exists():
        backup = dst.with_suffix(".cpp.regatebak")
        shutil.copy2(dst, backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cand, dst)
    matched = False
    try:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            report = Path(tf.name)
        cmd = [sys.executable, str(GATE), module, addr, "--ref-bin", str(ref_bin),
               "--body", str(size), "--report", str(report)]
        if update:
            cmd.append("--update")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        try:
            rep = json.loads(report.read_text())
        except Exception:
            rep = {}
        finally:
            report.unlink(missing_ok=True)
        matched = proc.returncode == 0
        return {"addr": addr, "rc": proc.returncode, **rep}
    finally:
        if not (matched and keep_on_match):
            dst.unlink(missing_ok=True)
            if backup is not None:
                shutil.move(str(backup), str(dst))
        elif backup is not None:
            backup.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--class", dest="cls", default="plain",
                    choices=["plain", "guard", "veneer", "ungateable", "any"],
                    help="which failure class to re-gate (default: plain)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N entries")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--max-candidates", type=int, default=0,
                    help="cap candidates tried per entry (0 = all)")
    ap.add_argument("--update", action="store_true", help="write verify=match on a hit")
    ap.add_argument("--addr-file", type=Path, default=None,
                    help="only these addresses, one per line (e.g. the match rows of a --tsv)")
    ap.add_argument("--tsv", type=Path, default=None)
    args = ap.parse_args(argv)

    only = None
    if args.addr_file is not None:
        only = {ln.split("\t")[0].strip() for ln in args.addr_file.read_text().splitlines()
                if ln.strip()}
        if not only:
            raise SystemExit(f"no addresses in {args.addr_file}")

    text = complexity.load_text(str(REPO / "baserom" / "main.nso"))
    if text is None:
        raise SystemExit("could not read baserom/main.nso")
    by = load_entries()
    ref_bin = find_ref_bin()

    targets = []
    for (module, addr), recs in sorted(by.items()):
        if any(r.get("outcome") == "match" for r in recs):
            continue
        size = recs[0]["body"]
        if only is not None and addr not in only:
            continue
        cls = classify(complexity.body_of(text, addr, size))
        if args.cls != "any" and cls != args.cls:
            continue
        cands = []
        for r in recs:
            p = ATTEMPTS / r["candidate"]
            if p.exists():
                cands.append(p)
        if not cands:
            continue
        if args.max_candidates:
            cands = cands[-args.max_candidates:]
        targets.append((module, addr, size, cands))
        if args.limit and len(targets) >= args.limit:
            break

    print(f"re-gating {len(targets)} entries of class {args.cls!r} "
          f"({sum(len(t[3]) for t in targets)} candidates)", flush=True)

    def work(item):
        module, addr, size, cands = item
        for i, cand in enumerate(reversed(cands), 1):    # newest first
            res = gate_one(cand, module, addr, size, ref_bin, args.update,
                           keep_on_match=args.update)
            if res.get("rc") == 0:
                return {"addr": addr, "size": size, "status": "match",
                        "cand": str(cand.name), "tried": i}
        res = gate_one(cands[-1], module, addr, size, ref_bin, False)
        return {"addr": addr, "size": size, "status": res.get("status", "error"),
                "cand": cands[-1].name, "tried": len(cands)}

    rows = []
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for i, res in enumerate(ex.map(work, targets), 1):
            rows.append(res)
            if i % 20 == 0:
                m = sum(1 for r in rows if r["status"] == "match")
                print(f"  {i}/{len(targets)}  matches so far {m}", flush=True)

    m = sum(1 for r in rows if r["status"] == "match")
    print(f"\nmatched {m}/{len(rows)} ({100*m/max(len(rows),1):.1f}%)")
    print("status:", collections.Counter(r["status"] for r in rows).most_common())
    if args.tsv:
        with args.tsv.open("w") as f:
            f.write("addr\tsize\tstatus\tcand\ttried\n")
            for r in rows:
                f.write(f"{r['addr']}\t{r['size']}\t{r['status']}\t{r['cand']}\t{r['tried']}\n")
        print("wrote", args.tsv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
