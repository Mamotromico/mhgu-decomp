"""Export the committed ledger as an **objdiff report** — decomp.dev's progress format.

decomp.dev (``encounter/decomp.dev``) does not scrape source: its bot downloads a GitHub
Actions artifact named ``<version>_report`` and parses the ``report.json`` inside it with
``objdiff_core::bindings::report::Report`` (the protobuf-derived schema in
``objdiff-core/protos/report.proto``, current ``REPORT_VERSION = 2``). This tool renders the
committed ledger as exactly that document, so the published number is derived from the one
shared predicate (``ledgerlib``) — never hand-authored. See ``docs/architecture.md`` →
*Progress metrics*.

Mapping (every field is the predicate in ``ledgerlib``; nothing is invented)
---------------------------------------------------------------------------
The site's two figures are *decompiled* (``matched_code``) and *fully linked*
(``complete_code``); both are code-byte percentages.

* ``matched_code`` / ``matched_functions`` ← ``decompiled(e)`` (``verify = match``).
* ``complete_code`` / ``complete_data`` ← ``enroll = complete``, the *build input* axis
  ("original bytes vs. our compiled object"). It is the ledger-expressible stand-in for the
  Linked metric: the whole-image ``reloc`` check refines it at build time and is, by design,
  derived rather than stored (see *Status layer & the shared "matched" predicate*).
* code = ``kind = function``; data = ``kind = data`` (literal pools living in ``.text`` stay
  data, because the entry's *kind*, not its block, decides).
* ``fuzzy_match_percent`` is the code match percent: an entry is byte-identical or it is not,
  so the ledger has no partial credit to report.

Categories are the ledger's ``module`` (one bar per module); the top-level ``measures`` are
what decomp.dev publishes. Per-unit detail (``units``, grouped by ``group``) is **omitted by
default**: the ledger's one-function-per-file default makes ``group`` one-per-function, so
emitting every unit inflates the artifact to hundreds of MB (267k groups / ~245 MB on the
seed) for detail decomp.dev does not surface. ``--units`` includes it for local inspection.

Usage::

    python3 tools/ledger/report.py                     # report for the committed ledger -> stdout
    python3 tools/ledger/report.py --out report.json   # write the artifact body
    python3 tools/ledger/report.py --units             # include per-group unit detail
    python3 tools/ledger/report.py --ledger FILE --compact

Exit codes::

    0  report emitted
    2  usage error (ledger does not exist)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ledgerlib import counted, decompiled, read_entries

REPO = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"

# objdiff REPORT_VERSION (objdiff-core/src/bindings/report.rs). v2 is emitted fully formed, so
# decomp.dev's Report::migrate() is a no-op (v0/v1 migration would otherwise recompute these).
REPORT_VERSION = 2

_COUNT_KEYS = (
    "total_code", "matched_code",
    "total_data", "matched_data",
    "total_functions", "matched_functions",
    "complete_code", "complete_data",
    "total_units", "complete_units",
)


def is_complete(e: dict) -> bool:
    """In the denominator and enrolled as our compiled object (the build-input axis)."""
    return counted(e) and e["enroll"] == "complete"


def _pct(numerator: float, denominator: float) -> float:
    """objdiff's convention: an empty denominator is 100%, not a division by zero."""
    return 100.0 if denominator == 0 else numerator / denominator * 100.0


def _counts(entries: list[dict]) -> dict:
    """Accumulate one bucket's byte/count totals (no percentages; see ``_finalize``)."""
    c = {k: 0 for k in _COUNT_KEYS}
    for e in entries:
        size = int(e["size"])
        if e["kind"] == "function":
            c["total_code"] += size
            c["total_functions"] += 1
            if decompiled(e):
                c["matched_code"] += size
                c["matched_functions"] += 1
        else:  # data
            c["total_data"] += size
            if decompiled(e):
                c["matched_data"] += size
        if is_complete(e):
            c["complete_code" if e["kind"] == "function" else "complete_data"] += size
    return c


def _finalize(c: dict) -> dict:
    """Turn raw counts into an objdiff ``Measures`` object (field order mirrors the proto)."""
    total_code, total_data = c["total_code"], c["total_data"]
    return {
        "fuzzy_match_percent": _pct(c["matched_code"], total_code),
        "total_code": total_code,
        "matched_code": c["matched_code"],
        "matched_code_percent": _pct(c["matched_code"], total_code),
        "total_data": total_data,
        "matched_data": c["matched_data"],
        "matched_data_percent": _pct(c["matched_data"], total_data),
        "total_functions": c["total_functions"],
        "matched_functions": c["matched_functions"],
        "matched_functions_percent": _pct(c["matched_functions"], c["total_functions"]),
        "complete_code": c["complete_code"],
        "complete_code_percent": _pct(c["complete_code"], total_code),
        "complete_data": c["complete_data"],
        "complete_data_percent": _pct(c["complete_data"], total_data),
        "total_units": c["total_units"],
        "complete_units": c["complete_units"],
    }


def _item(e: dict) -> dict:
    """One ``ReportItem`` (a function or a data section)."""
    item = {
        "name": e["name"],
        "size": int(e["size"]),
        "fuzzy_match_percent": 100.0 if decompiled(e) else 0.0,
    }
    if e["addr"]:
        item["metadata"] = {"virtual_address": int(e["addr"], 16)}
    return item


def build(entries: list[dict], include_units: bool = False) -> dict:
    """Render ledger entries as an objdiff ``Report`` (v2) document.

    ``include_units`` adds per-``group`` unit detail; it is off by default because the ledger's
    one-function-per-file default makes that detail enormous (see the module docstring).
    """
    counted_entries = [e for e in entries if counted(e)]

    # Group by (module, group): the unit is a translation unit, its category is the module.
    groups: dict[tuple[str, str], list[dict]] = {}
    for e in counted_entries:
        groups.setdefault((e["module"], e["group"]), []).append(e)

    units = []
    complete_by_module: dict[str, list[int]] = {}  # module -> [total, complete]
    for (module, group), es in sorted(groups.items()):
        complete = all(is_complete(e) for e in es)
        tally = complete_by_module.setdefault(module, [0, 0])
        tally[0] += 1
        tally[1] += 1 if complete else 0
        if include_units:
            c = _counts(es)
            c["total_units"] = 1
            c["complete_units"] = 1 if complete else 0
            unit = {"name": group, "measures": _finalize(c)}
            functions = [_item(e) for e in es if e["kind"] == "function"]
            sections = [_item(e) for e in es if e["kind"] == "data"]
            if functions:
                unit["functions"] = functions
            if sections:
                unit["sections"] = sections
            unit["metadata"] = {"complete": complete, "progress_categories": [module]}
            units.append(unit)

    measures = _counts(counted_entries)
    measures["total_units"] = sum(t for t, _c in complete_by_module.values())
    measures["complete_units"] = sum(c for _t, c in complete_by_module.values())

    # One category per module, aggregated from that module's units.
    by_module: dict[str, list[dict]] = {}
    for (module, _group), es in sorted(groups.items()):
        by_module.setdefault(module, []).extend(es)
    categories = []
    for module, es in sorted(by_module.items()):
        c = _counts(es)
        c["total_units"], c["complete_units"] = complete_by_module[module]
        categories.append({"id": module, "name": module, "measures": _finalize(c)})

    report = {"measures": _finalize(measures), "version": REPORT_VERSION,
              "categories": categories}
    if include_units:
        report["units"] = units
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER,
                    help="committed ledger (default config/main/ledger.tsv)")
    ap.add_argument("--out", type=Path, default=None,
                    help="write the report here (default: stdout)")
    ap.add_argument("--units", action="store_true",
                    help="include per-group unit detail (large; omitted by default)")
    ap.add_argument("--compact", action="store_true",
                    help="emit compact JSON (no indentation)")
    args = ap.parse_args(argv)

    if not args.ledger.exists():
        print(f"error: {args.ledger}: does not exist", file=sys.stderr)
        return 2

    report = build(read_entries(args.ledger), include_units=args.units)
    if args.compact:
        text = json.dumps(report, separators=(",", ":"))
    else:
        text = json.dumps(report, indent=2)
    text += "\n"

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        m = report["measures"]
        print(f"report: {args.out}  "
              f"decompiled {m['matched_code_percent']:.2f}%  "
              f"linked {m['complete_code_percent']:.2f}%", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
