"""Report the recurring instruction shapes among the pending corpus — "what to template next?".

The loop templates trivial leaf shapes before it calls the model (`tools/ledger/templates.py`).
Which shapes to add next should be **measured, not guessed** (the sm64ds lesson: its mwccarm/ARM9
rule list does not port wholesale). This is that measurement: it filters the ledger to pending
functions, resolves each body's bytes, keeps the easy clean leaves (tier 0, from
`tools/ledger/complexity.py`), decodes each to a normalized signature (`tools/ledger/shapes.py`),
and prints the shapes that recur most — excluding the ones templates already cover, so the output
is exactly the un-templated opportunity, ranked by frequency.

It is an **analysis CLI** (a thin driver over the pure `shapes`/`complexity` libraries), not part
of the reconstruction loop: it only reads, and it changes no state. It is deliberately *evidence*,
not authority — a frequent shape is a candidate for a rule, and the byte gate still decides.

Usage::

    python3 tools/ledger/shape_report.py                    # top 40 un-templated tier-0 shapes
    python3 tools/ledger/shape_report.py --limit 0          # every distinct shape
    python3 tools/ledger/shape_report.py --covered          # include template-covered shapes
    python3 tools/ledger/shape_report.py --tier 1           # a different tier
    python3 tools/ledger/shape_report.py --json             # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))
sys.path.insert(0, str(REPO / "tools" / "loop"))

import bundle
import complexity
import shapes
import templates
from ledgerlib import read_entries

DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_INVENTORY = REPO / "baserom" / "work" / "inventory" / "inventory.tsv"
DEFAULT_NSO = REPO / "baserom" / "main.nso"


def gather(entries: list[dict], text: bytes, sizes: dict[str, int],
           blocks: list[tuple[int, int]], tier: int,
           include_covered: bool) -> tuple[Counter, dict[tuple, list], dict]:
    """Histogram the ``tier`` pending bodies' signatures, plus per-shape examples and stats.

    Tiering reuses the loop's own ordering key (``complexity.make_key``), so the report and the
    auto-selector agree on what "tier 0" means by construction. A body is skipped when it is
    unreadable or already emitted by a template (unless ``include_covered``). ``examples`` maps a
    signature to the first few ``(addr, size)``.
    """
    key = complexity.make_key(text, sizes, blocks)
    stats = Counter()
    sigs: Counter = Counter()
    examples: dict[tuple, list] = {}
    for e in entries:
        if e["kind"] != "function" or e["verify"] != "none":
            continue
        got, size = key(e)                       # (tier, body len) or (unreadable, size)
        if got == 3:
            stats["unreadable"] += 1
            continue
        stats["pending"] += 1
        stats[f"tier{got}"] += 1
        if got != tier:
            continue
        stats["in_tier"] += 1
        body = complexity.body_of(text, e["addr"], size)
        if body is None:                         # key() said readable; guard defensively
            continue
        if templates.propose(body, e["name"]) is not None:
            stats["covered"] += 1
            if not include_covered:
                continue
        sig = shapes.signature(body)
        sigs[sig] += 1
        examples.setdefault(sig, [])
        if len(examples[sig]) < 3:
            examples[sig].append((e["addr"], len(body)))
    return sigs, examples, stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO)
    ap.add_argument("--tier", type=int, default=0, help="difficulty tier to report (default: 0)")
    ap.add_argument("--limit", type=int, default=40, help="shapes to print; 0 = all (default: 40)")
    ap.add_argument("--covered", action="store_true",
                    help="include shapes templates already cover")
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = ap.parse_args(argv)

    if not args.ledger.exists():
        print(f"error: missing ledger {args.ledger}", file=sys.stderr)
        return 2
    text = complexity.load_text(args.nso)
    if text is None:
        print(f"error: reference .text unavailable ({args.nso})", file=sys.stderr)
        return 2
    sizes = (bundle.parse_inventory(args.inventory.read_text())
             if args.inventory.exists() else {})
    blocks = complexity.load_blocks(args.inventory.with_name("inventory.blocks.tsv"))

    entries = read_entries(args.ledger)
    sigs, examples, stats = gather(entries, text, sizes, blocks, args.tier, args.covered)

    ranked = sigs.most_common(args.limit if args.limit else None)
    if args.json:
        print(json.dumps({
            "tier": args.tier,
            "stats": dict(stats),
            "distinct_shapes": len(sigs),
            "shapes": [{"count": n, "signature": shapes.render_sig(sig),
                        "examples": [a for a, _ in examples[sig]]} for sig, n in ranked],
        }, indent=2, ensure_ascii=False))
        return 0

    print(f"pending functions: {stats['pending']}  (unreadable: {stats['unreadable']})")
    dist = ", ".join(f"tier{t}={stats[f'tier{t}']}" for t in range(4) if stats[f"tier{t}"])
    print(f"tier distribution: {dist}")
    untemplated = sum(sigs.values())
    print(f"tier {args.tier} bodies: {stats['in_tier']}  (template-covered: {stats['covered']}; "
          f"un-templated: {untemplated} across {len(sigs)} distinct shapes, "
          f"top {len(ranked)} shown)")
    print()
    print(f"{'count':>6}  {'len':>4}  signature")
    print("-" * 120)
    for sig, n in ranked:
        ex = examples[sig]
        print(f"{n:>6}  {ex[0][1]:>4}  {shapes.render_sig(sig)}"
              f"    {', '.join(a for a, _ in ex)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
