"""A versioned, stratified benchmark of unmatched functions — the fixed evaluation set.

Plan Batch 2. Later model-context experiments (Batch 3) claim improvements against this
set; without a frozen, cohort-tagged sample, "the new prompt matched more" is anecdote —
the dynamic queue's composition shifts between runs and free wins (re-gated candidates,
deterministic templates) get silently credited to whatever change happened to run that day.

A benchmark is a **document**: a named JSON file under the git-ignored
``baserom/work/benchmark/`` recording what it was built from (input fingerprints), how it
was sampled (params), and its entries with per-entry cohort tags and a dev/holdout split.
The document carries a content digest; :func:`verify_document` recomputes it, and ``show``
compares the recorded inputs against the *current* files — a benchmark built under another
compiler pin or gate version is flagged stale before it is used, never silently.

Population: ``kind=function`` ledger entries that are still unmatched, readable, not
linker veneers, and verifiable by the gate today (``complexity.gateable``) — the same
predicate ``run.py --matchable`` selects on, so every sampled entry can actually match.

Cohorts (plan *Success measures* #4) are **tags**, not a partition — one entry can carry
several. Feature detection is byte-level heuristics over the A32 body (documented per
function), reusing ``complexity`` where a signal already exists:

    size bucket  <=16B / 17-32B / 33-64B / >64B (body length)
    leaf|calls   ``complexity.has_call`` (a BL/BLX anywhere)
    import_call  an immediate BL whose target is a ledger ``import-stub`` address
                 (register-indirect import calls are not visible statically — untagged)
    pool         ``complexity.has_pool_load`` (reads a literal-pool word)
    preindexed   a ``[Rn, …]!`` writeback (P=1 and W=1 on a data transfer)
    fpneon       a VFP/NEON/coprocessor word (cond=1111 or coprocessor class 110/111)
    control      a conditional ``B`` (cond != AL) — a loop or if
    guard        a conditional ``bxCC lr`` — the documented known-hard class
                 (``regate_candidates.has_cond_return``)

Sampling is **round-robin over cohort lists** (one list per tag, each sorted by address,
fixed rotation order): every cohort with any population is covered before unrelated entries
repeat, size buckets lead the rotation, and the result is deterministic for identical
inputs. The dev/holdout split is a pure hash of the salt and the entry key, so it survives
re-sorts and needs no state.

Usage::

    python3 tools/loop/benchmark.py create --name v1 --total 400
    python3 tools/loop/benchmark.py show --name v1          # integrity + input freshness
    python3 tools/loop/benchmark.py addrs --name v1 --split dev   # for run.py/regate
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))

import bundle
import complexity
import nearmiss
from bytegate import GATE_VERSION
from ledgerlib import counted, read_entries
from regate_candidates import has_cond_return

DEFAULT_DIR = REPO / "baserom" / "work" / "benchmark"
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_NSO = REPO / "baserom" / "main.nso"
DEFAULT_INVENTORY = REPO / "baserom" / "work" / "inventory" / "inventory.tsv"
DEFAULT_TOOLCHAIN = REPO / "config" / "toolchain.json"

FORMAT = 1

# The rotation order for sampling: size first (the primary difficulty axis), then the
# binary features, known-hard last.
COHORT_ORDER = ("<=16B", "17-32B", "33-64B", ">64B",
                "leaf", "calls",
                "pool", "preindexed", "fpneon", "control", "import_call", "guard")


# --- pure helpers (unit-tested) -------------------------------------------------------

def size_bucket(body_len: int) -> str:
    """The size cohort label for a body length."""
    if body_len <= 16:
        return "<=16B"
    if body_len <= 32:
        return "17-32B"
    if body_len <= 64:
        return "33-64B"
    return ">64B"


def has_preindexed_writeback(body: bytes) -> bool:
    """A pre-indexed ``[Rn, …]!`` writeback: P=1 and W=1 on a single or halfword transfer."""
    for off in range(0, len(body) - 3, 4):
        w = int.from_bytes(body[off:off + 4], "little")
        if w & 0xF0000000 == 0xF0000000:
            continue
        if (w & 0x0C000000) == 0x04000000 and (w & 0x01200000) == 0x01200000:
            return True
        if (w & 0x0E000090) == 0x00000090 and (w & 0x01200000) == 0x01200000:
            return True
    return False


def has_fp_neon(body: bytes) -> bool:
    """A VFP/NEON/coprocessor word: the unconditional (cond=1111) prefix or coprocessor
    transfer/arithmetic classes 110/111 (``vldr``/``vstr`` are class 110; VFP data ops are
    class 111; NEON data ops use the cond=1111 prefix). MCR/MRC are rare in ``.text`` —
    acceptable for a cohort tag, never a verdict."""
    for off in range(0, len(body) - 3, 4):
        w = int.from_bytes(body[off:off + 4], "little")
        if w & 0xF0000000 == 0xF0000000:
            return True
        if (w >> 25) & 0x7 in (0b110, 0b111):
            return True
    return False


def has_conditional_branch(body: bytes) -> bool:
    """A conditional ``B`` (cond != AL) — a loop or an if."""
    for off in range(0, len(body) - 3, 4):
        w = int.from_bytes(body[off:off + 4], "little")
        if w & 0xF0000000 == 0xF0000000:
            continue
        if (w & 0x0F000000) == 0x0A000000 and (w >> 28) != 0xE:
            return True
    return False


def call_targets(body: bytes, addr: str) -> list[int]:
    """Absolute targets of immediate ``BL`` words (register-indirect calls are not visible
    statically and are not tagged)."""
    base = int(addr, 16)
    targets = []
    for off in range(0, len(body) - 3, 4):
        w = int.from_bytes(body[off:off + 4], "little")
        if w & 0xF0000000 == 0xF0000000:
            continue
        if (w & 0x0F000000) == 0x0B000000:
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            targets.append(base + off + 8 + (imm << 2))
    return targets


def cohorts_for(entry: dict, body: bytes, stub_addrs: set[int]) -> list[str]:
    """The cohort tags for one eligible entry (see the module doc for the tag meanings)."""
    tags = [size_bucket(len(body))]
    if complexity.has_call(body):
        tags.append("calls")
    else:
        tags.append("leaf")
    if complexity.has_pool_load(body):
        tags.append("pool")
    if has_preindexed_writeback(body):
        tags.append("preindexed")
    if has_fp_neon(body):
        tags.append("fpneon")
    if has_conditional_branch(body):
        tags.append("control")
    if any(t in stub_addrs for t in call_targets(body, entry["addr"])):
        tags.append("import_call")
    if has_cond_return(body):
        tags.append("guard")
    return tags


def stratified_sample(candidates: list[dict], total: int) -> list[dict]:
    """Round-robin over per-cohort lists (sorted by ``(module, addr)``, fixed rotation).

    Every cohort with any population contributes before an entry already picked repeats, so
    rare tags (fpneon, guard, import_call) are covered at least once when ``total`` allows;
    size buckets lead the rotation. Deterministic for identical input order.
    """
    by_tag: dict[str, list[dict]] = {}
    for c in candidates:
        for tag in c["cohorts"]:
            by_tag.setdefault(tag, []).append(c)
    lists = [by_tag[tag] for tag in COHORT_ORDER if tag in by_tag]
    cursors = [0] * len(lists)
    picked: list[dict] = []
    seen: set[tuple[str, str]] = set()
    while len(picked) < total:
        progressed = False
        for li, cohort in enumerate(lists):
            if len(picked) >= total:
                break
            while cursors[li] < len(cohort):
                cand = cohort[cursors[li]]
                cursors[li] += 1
                key = (cand["module"], cand["addr"])
                if key not in seen:
                    seen.add(key)
                    picked.append(cand)
                    progressed = True
                    break
        if not progressed:
            break
    return picked


def assign_split(module: str, addr: str, salt: str, holdout_fraction: float) -> str:
    """The dev/holdout assignment: a pure hash of the salt and the entry key."""
    h = hashlib.sha256(f"{salt}/{module}/{addr}".encode("utf-8")).digest()[0]
    return "holdout" if h < holdout_fraction * 256 else "dev"


def document_digest(doc: dict) -> str:
    """The content digest over everything except the digest itself (canonical JSON)."""
    payload = {k: v for k, v in doc.items() if k != "digest"}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def verify_document(doc: dict) -> bool:
    """Whether the digest matches the content — a tampered or truncated file fails closed."""
    return isinstance(doc, dict) and doc.get("digest") == document_digest(doc)


def build_document(*, name: str, entries: list[dict], text: bytes,
                   sizes: dict[str, int], inputs: dict, total: int,
                   holdout_fraction: float, salt: str, now: str) -> dict:
    """Assemble the benchmark document (pure; the CLI gathers the inputs).

    ``entries`` is the ledger, ``text`` the reference ``.text``, ``sizes`` the inventory's
    body sizes (``bundle.parse_inventory``). Population: unmatched, counted, readable,
    non-veneer, gateable function entries.
    """
    stub_addrs = {int(e["addr"], 16) for e in entries
                  if e["kind"] == "import-stub" and e.get("addr")}
    candidates = []
    for e in entries:
        if e["kind"] != "function" or e["verify"] != "none" or not counted(e):
            continue
        size = sizes.get(e["addr"]) or int(e["size"] or 0)
        body = complexity.body_of(text, e["addr"], size)
        if body is None or complexity.is_veneer(body) or not complexity.gateable(body):
            continue
        candidates.append({"module": e["module"], "addr": e["addr"], "name": e["name"],
                           "partition": int(e["size"]), "body": len(body),
                           "cohorts": cohorts_for(e, body, stub_addrs)})
    candidates.sort(key=lambda c: (c["module"], c["addr"]))
    picked = stratified_sample(candidates, total)
    out_entries = [{**c, "split": assign_split(c["module"], c["addr"], salt,
                                               holdout_fraction)} for c in picked]
    doc = {
        "format": FORMAT,
        "name": name,
        "created": now,
        "inputs": inputs,
        "params": {"total": total, "holdout_fraction": holdout_fraction, "salt": salt},
        "counts": {
            "eligible": len(candidates),
            "selected": len(out_entries),
            "dev": sum(1 for e in out_entries if e["split"] == "dev"),
            "holdout": sum(1 for e in out_entries if e["split"] == "holdout"),
            "cohorts": {tag: sum(1 for e in out_entries if tag in e["cohorts"])
                        for tag in COHORT_ORDER},
        },
        "entries": out_entries,
    }
    doc["digest"] = document_digest(doc)
    return doc


# --- input fingerprints (impure) ------------------------------------------------------

def file_sha256(path: Path) -> str | None:
    """The content fingerprint of a config file, or ``None`` when it cannot be read."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def nso_fingerprint(path: Path) -> dict | None:
    """The NSO identity in the gotmap/refcache convention (``path``/``size``/``mtime_ns``)."""
    try:
        st = Path(path).stat()
    except OSError:
        return None
    return {"path": str(Path(path).resolve()), "size": st.st_size, "mtime_ns": st.st_mtime_ns}


def collect_inputs(ledger: Path, inventory: Path, toolchain: Path, nso: Path) -> dict:
    """Fingerprint every input the benchmark is a function of."""
    return {
        "ledger_sha256": file_sha256(ledger),
        "inventory_sha256": file_sha256(inventory),
        "toolchain_sha256": file_sha256(toolchain),
        "eval_pin": nearmiss.eval_pin(toolchain),
        "gate_version": GATE_VERSION,
        "nso": nso_fingerprint(nso),
    }


def freshness(doc: dict, *, ledger: Path, inventory: Path, toolchain: Path,
              nso: Path) -> list[tuple[str, str, str]]:
    """(aspect, recorded, current) triples — 'current' or 'STALE' per input."""
    now = collect_inputs(ledger, inventory, toolchain, nso)
    rows = []
    for aspect in ("ledger_sha256", "inventory_sha256", "toolchain_sha256",
                   "eval_pin", "gate_version"):
        recorded = doc.get("inputs", {}).get(aspect)
        current = now.get(aspect)
        rows.append((aspect, recorded, current))
    recorded_nso = doc.get("inputs", {}).get("nso") or {}
    current_nso = now.get("nso") or {}
    nso_state = "current" if recorded_nso == current_nso else "STALE"
    rows.append(("nso", json.dumps(recorded_nso, sort_keys=True),
                 f"{json.dumps(current_nso, sort_keys=True)}  [{nso_state}]"))
    return rows


# --- storage --------------------------------------------------------------------------

def safe_name(name: str) -> str:
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise ValueError(f"unsafe benchmark name: {name!r}")
    return name


def benchmark_path(directory: Path, name: str) -> Path:
    return Path(directory) / f"{safe_name(name)}.json"


def save_document(directory: Path, doc: dict) -> Path:
    """Atomic write (temp + rename) per the cache conventions."""
    path = benchmark_path(directory, doc["name"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    os.replace(tmp, path)
    return path


def load_document(directory: Path, name: str) -> dict:
    path = benchmark_path(directory, name)
    if not path.exists():
        raise ValueError(f"no benchmark named {name!r} under {directory} "
                         f"(create it first: benchmark.py create --name {name})")
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"{path}: corrupt benchmark: {e}") from e
    if not verify_document(doc):
        raise ValueError(f"{path}: digest mismatch — the benchmark is tampered or truncated")
    return doc


# --- CLI ------------------------------------------------------------------------------

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("create", "show", "addrs"))
    ap.add_argument("--name", required=True)
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO)
    ap.add_argument("--toolchain", type=Path, default=DEFAULT_TOOLCHAIN)
    ap.add_argument("--total", type=int, default=400,
                    help="entries to select (default 400; more than eligible selects all)")
    ap.add_argument("--holdout-fraction", type=float, default=0.2,
                    help="fraction assigned to the holdout split (default 0.2)")
    ap.add_argument("--salt", default=None,
                    help="the split salt (default: the benchmark name)")
    ap.add_argument("--split", choices=("dev", "holdout", "all"), default="all",
                    help="with 'addrs': which split to print (default all)")
    args = ap.parse_args(argv)

    if not 0 < args.holdout_fraction < 1:
        print("error: --holdout-fraction must be in (0, 1)", file=sys.stderr)
        return 2

    if args.command == "create":
        if args.total < 1:
            print("error: --total must be >= 1", file=sys.stderr)
            return 2
        if not args.ledger.exists():
            print(f"error: missing ledger {args.ledger}", file=sys.stderr)
            return 2
        text = complexity.load_text(args.nso)
        if text is None:
            print(f"error: could not read reference .text from {args.nso}", file=sys.stderr)
            return 2
        sizes = (bundle.parse_inventory(args.inventory.read_text())
                 if args.inventory.exists() else {})
        salt = args.salt or args.name
        doc = build_document(name=safe_name(args.name), entries=read_entries(args.ledger),
                             text=text, sizes=sizes,
                             inputs=collect_inputs(args.ledger, args.inventory,
                                                   args.toolchain, args.nso),
                             total=args.total, holdout_fraction=args.holdout_fraction,
                             salt=salt, now=utc_now())
        path = save_document(args.dir, doc)
        c = doc["counts"]
        print(f"benchmark {doc['name']}: {c['selected']} entries "
              f"({c['dev']} dev / {c['holdout']} holdout) of {c['eligible']} eligible; "
              f"digest {doc['digest']}")
        print(f"  cohorts: " + ", ".join(f"{t}={n}" for t, n in c["cohorts"].items() if n))
        print(f"wrote {path}")
        return 0

    try:
        doc = load_document(args.dir, args.name)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.command == "show":
        c = doc["counts"]
        print(f"benchmark {doc['name']}  digest {doc['digest']}  created {doc['created']}")
        print(f"  {c['selected']} entries ({c['dev']} dev / {c['holdout']} holdout) "
              f"of {c['eligible']} eligible")
        p = doc["params"]
        print(f"  params: total={p['total']} holdout_fraction={p['holdout_fraction']} "
              f"salt={p['salt']!r}")
        print("  inputs:")
        for aspect, recorded, current in freshness(doc, ledger=args.ledger,
                                                   inventory=args.inventory,
                                                   toolchain=args.toolchain, nso=args.nso):
            marker = "" if str(current).endswith("[current]") or recorded == current else "  <-- STALE"
            print(f"    {aspect}: {recorded} -> {current}{marker}")
        print("  cohorts (selected):")
        for tag in COHORT_ORDER:
            dev = sum(1 for e in doc["entries"] if tag in e["cohorts"] and e["split"] == "dev")
            ho = sum(1 for e in doc["entries"] if tag in e["cohorts"] and e["split"] == "holdout")
            if dev or ho:
                print(f"    {tag:<12} {dev + ho:>4}  (dev {dev} / holdout {ho})")
        return 0

    # addrs
    chosen = [e for e in doc["entries"]
              if args.split == "all" or e["split"] == args.split]
    for e in sorted(chosen, key=lambda e: (e["module"], e["addr"])):
        print(e["addr"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
