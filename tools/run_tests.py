"""Run the whole test suite in one command.

Every test file is a plain ``unittest`` script that also runs standalone (``python3
tests/loop/test_bundle.py``) — handy while writing one thing. This runner gives the
one-command whole-suite entry point without adding a dependency: it discovers every
``tests/**/test_*.py`` and runs each in its own subprocess (isolation, and exactly the
documented invocation), then reports a per-file PASS/FAIL summary.

Deliberately stdlib-only, matching the rest of the tooling: no pytest, no config file, no
plugin. Tests are discovered by path, so there is nothing to register.

Usage::

    python3 tools/run_tests.py              # run everything
    python3 tools/run_tests.py loop         # only files whose path contains 'loop'
    python3 tools/run_tests.py loop ledger  # several filters (OR)
    python3 tools/run_tests.py -v           # show each file's full output
    python3 tools/run_tests.py --list       # list what would run, then exit
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TESTS = REPO / "tests"


def discover(filters: list[str]) -> list[Path]:
    """All ``tests/**/test_*.py`` files, sorted; optionally filtered by path substring."""
    files = sorted(p for p in TESTS.rglob("test_*.py") if p.is_file())
    if filters:
        files = [p for p in files if any(f in p.as_posix() for f in filters)]
    return files


def run(path: Path, verbose: bool) -> bool:
    """Run one test file in a subprocess; print its result. Return whether it passed."""
    result = subprocess.run([sys.executable, str(path)], cwd=REPO,
                            capture_output=True, text=True)
    ok = result.returncode == 0
    if verbose:
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    print(f"  {'PASS' if ok else 'FAIL'}  {path.relative_to(REPO)}")
    if not ok:
        tail = (result.stdout + result.stderr).strip().splitlines()[-40:]
        for line in tail:
            print(f"        {line}")
    return ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("filters", nargs="*", help="only files whose path contains a filter")
    ap.add_argument("-v", "--verbose", action="store_true", help="show each file's output")
    ap.add_argument("--list", action="store_true", help="list discovered files and exit")
    args = ap.parse_args(argv)

    files = discover(args.filters)
    if not files:
        suffix = f" matching {args.filters}" if args.filters else ""
        print(f"no test files found{suffix}", file=sys.stderr)
        return 1
    if args.list:
        for path in files:
            print(path.relative_to(REPO))
        return 0

    print(f"running {len(files)} test file(s)")
    passed = sum(1 for path in files if run(path, args.verbose))
    print(f"{passed}/{len(files)} file(s) passed")
    return 0 if passed == len(files) else 1


if __name__ == "__main__":
    raise SystemExit(main())
