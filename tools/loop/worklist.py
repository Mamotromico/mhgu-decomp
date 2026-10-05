"""The reconstruction loop's queue: the committed ledger, filtered and ordered.

There is **no separate worklist file** (``docs/llm-harness-design.md`` → *Worklist — the
ledger is the queue*). The committed ledger *is* the worklist: selecting work is a pure query
over it, filtered to entries still needing reconstruction (default: ``kind=function`` and
``verify=none``). Because selection is derived, the queue updates itself as the gate flips
``verify`` — there is no second artifact to drift.

Ordering is deterministic — ``(module, addr)``, which is the ledger's own order — so two runs
over the same ledger yield the same queue, and a resume is just "start where you stopped".
``addr`` is invariant-validated as zero-padded 8-hex lowercase, so its lexical order is also
its numeric order; no parsing is needed to sort.

This module is the selector only: it reads the ledger, filters, orders, and reports. It never
writes — not the ledger, not ``src/`` — so it stays safe to run at any time.

Usage::

    python3 tools/loop/worklist.py                     # count + first 20 pending functions
    python3 tools/loop/worklist.py --limit 0           # the whole queue
    python3 tools/loop/worklist.py --next              # just the next entry (module addr name)
    python3 tools/loop/worklist.py --verify any --json # inspect the whole ledger as JSON
    python3 tools/loop/worklist.py --module main --limit 5
    python3 tools/loop/worklist.py --skip-existing     # drop groups already drawn in src/
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))

from ledgerlib import read_entries  # noqa: E402

DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_BUILD_CONFIG = REPO / "config" / "build.json"
DEFAULT_KIND = "function"
DEFAULT_VERIFY = "none"
DEFAULT_LIMIT = 20

# The values a filter accepts to mean "do not constrain on this axis".
ANY = ("any", "*", "")


# --- pure helpers (unit-tested) -------------------------------------------------------

def allowed(value: str | Iterable[str] | None) -> set[str] | None:
    """Normalize a filter to a set of allowed values, or ``None`` for "any".

    Accepts a single value, a comma-separated string, an iterable, or ``None`` / ``""`` /
    ``"any"`` / ``"*"`` to mean no constraint. This lets one helper serve ``--kind``,
    ``--verify`` and ``--module`` uniformly.
    """
    if value is None:
        return None
    if isinstance(value, str):
        if value in ANY:
            return None
        return {part.strip() for part in value.split(",") if part.strip()}
    return set(value) or None


def sort_key(entry: dict) -> tuple[str, str]:
    """The deterministic queue order: ``(module, addr)``.

    ``addr`` is 8-hex lowercase (a ledger invariant), so lexical order equals address order
    and no parse is needed. Externals carry an empty ``addr`` and sort first, which is
    harmless: they are excluded by the default ``kind`` filter.
    """
    return entry["module"], entry["addr"]


def source_path(entry: dict, src_root: Path) -> Path:
    """The translation-unit path a candidate for ``entry`` would be written to.

    ``src_root`` is the resolved source root (e.g. ``<repo>/src``), not the relative name;
    inject it so this stays a pure function with no knowledge of the build layout.
    """
    return Path(src_root) / entry["module"] / f"{entry['group']}.cpp"


def select(entries: list[dict], *, kind: str | Iterable[str] | None = DEFAULT_KIND,
           verify: str | Iterable[str] | None = DEFAULT_VERIFY,
           module: str | Iterable[str] | None = None,
           drop: Callable[[dict], bool] | None = None) -> list[dict]:
    """Filter the ledger into an ordered worklist.

    ``kind``, ``verify`` and ``module`` are each a value, a comma-separated string, an
    iterable, or ``None``/``"any"`` for no constraint (see ``allowed``). ``drop`` is an
    optional predicate: entries it returns true for are removed (the CLI uses it for
    ``--skip-existing``, keeping this function free of any filesystem access). The result is
    sorted by ``sort_key`` and is a new list, so the caller's ``entries`` is left untouched.
    """
    kinds = allowed(kind)
    verifies = allowed(verify)
    modules = allowed(module)
    chosen = [
        e for e in entries
        if (kinds is None or e["kind"] in kinds)
        and (verifies is None or e["verify"] in verifies)
        and (modules is None or e["module"] in modules)
        and (drop is None or not drop(e))
    ]
    chosen.sort(key=sort_key)
    return chosen


def source_root(build_config: Path, default: str = "src") -> str:
    """The source-root name from the shared build layout (``config/build.json``).

    Read inline, matching the byte gate's precedent, so both agree on the one shared file
    rather than on a loader.
    """
    if not build_config.exists():
        return default
    return json.loads(build_config.read_text()).get("source_root", default)


# --- CLI ------------------------------------------------------------------------------

def format_row(entry: dict) -> str:
    return (f"  {entry['addr']}  {entry['name']:<24}  {entry['group']:<24}  "
            f"{entry['block']:<8}  {entry['size']:>6} B")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--kind", default=DEFAULT_KIND,
                    help="function|data|external|any (default: function)")
    ap.add_argument("--verify", default=DEFAULT_VERIFY,
                    help="none|behaviour|match|any (default: none)")
    ap.add_argument("--module", default=None, help="restrict to one or more modules")
    ap.add_argument("--build-config", type=Path, default=DEFAULT_BUILD_CONFIG,
                    help="build layout, for --skip-existing's source root")
    ap.add_argument("--repo", type=Path, default=REPO,
                    help="repo root the source root is relative to")
    ap.add_argument("--skip-existing", action="store_true",
                    help="drop entries whose translation unit src/<module>/<group>.cpp exists")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                    help="max rows to print; 0 = all (default: 20)")
    ap.add_argument("--next", action="store_true",
                    help="print only the next entry as 'module<TAB>addr<TAB>name'")
    ap.add_argument("--json", action="store_true", help="emit the selected entries as JSON")
    args = ap.parse_args(argv)

    if not args.ledger.exists():
        print(f"error: missing ledger {args.ledger}", file=sys.stderr)
        return 2
    if args.limit < 0:
        ap.error("--limit must be >= 0")

    entries = read_entries(args.ledger)
    drop = None
    if args.skip_existing:
        src_root = args.repo / source_root(args.build_config)
        drop = lambda e: source_path(e, src_root).exists()
    queue = select(entries, kind=args.kind, verify=args.verify, module=args.module, drop=drop)

    if args.next:
        if not queue:
            print("error: worklist is empty", file=sys.stderr)
            return 1
        e = queue[0]
        print(f"{e['module']}\t{e['addr']}\t{e['name']}")
        return 0

    if args.json:
        shown = queue if args.limit == 0 else queue[:args.limit]
        print(json.dumps(shown, indent=2, ensure_ascii=False))
        return 0

    shown = queue if args.limit == 0 else queue[:args.limit]
    print(f"worklist: {len(queue)} entr{'y' if len(queue) == 1 else 'ies'} "
          f"(kind={args.kind}, verify={args.verify}"
          + (f", module={args.module}" if args.module else "")
          + (", skip-existing" if args.skip_existing else "") + ")")
    for e in shown:
        print(format_row(e))
    if len(shown) < len(queue):
        print(f"  ... {len(queue) - len(shown)} more (use --limit 0 or --next)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
