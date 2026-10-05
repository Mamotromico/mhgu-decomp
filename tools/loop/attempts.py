"""The attempt log: an append-only, parent-linked record of every reconstruction attempt.

Every attempt is kept — a near miss is evidence, not waste (``AGENTS.md``) — under the
git-ignored ``baserom/work/attempts/``:

::

    baserom/work/attempts/
      log.jsonl                 # append-only; one JSON object per attempt
      <module>/<addr>/001.cpp   # the candidate that attempt produced

Two properties matter:

* **Append-only.** Records are never rewritten. The log *is* the history; the near-miss bank
  (``nearmiss.py``) is the derived best-of view.
* **Parent-linked.** Each attempt points at the previous attempt for the same ``(module,
  addr)`` (``parent``), so retries form a tree — an attempt with no parent is the first for
  that entry. ``append`` computes the parent automatically unless one is supplied.

The candidate blob path is derived from the ledger (module/addr) and the attempt id; a
component containing a path separator or ``..`` is refused, so the ledger cannot make the log
write outside the store (the same containment rule the driver applies to ``src/``).

Run standalone to inspect the log::

    python3 tools/loop/attempts.py                 # summary per entry + a total
    python3 tools/loop/attempts.py --module main   # one module
    python3 tools/loop/attempts.py --entry 601a72e4
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_STORE = REPO / "baserom" / "work" / "attempts"


class AttemptError(Exception):
    """An attempt could not be recorded (unsafe path, corrupt log)."""


# --- pure helpers (unit-tested) -------------------------------------------------------

def safe_component(value: str) -> str:
    """A ledger path component that is safe to join under the store (no traversal)."""
    if not value or "/" in value or "\\" in value or value in (".", ".."):
        raise AttemptError(f"unsafe path component: {value!r}")
    return value


def candidate_relpath(module: str, addr: str, attempt_id: int) -> Path:
    """The store-relative path of an attempt's candidate blob."""
    return Path(safe_component(module)) / safe_component(addr) / f"{attempt_id:03d}.cpp"


def next_id(records: list[dict]) -> int:
    """The next 1-based attempt id (max existing id + 1)."""
    return max((int(r.get("id", 0)) for r in records), default=0) + 1


def parent_for(records: list[dict], module: str, addr: str) -> int | None:
    """The id of the most recent attempt for ``(module, addr)``, or ``None`` (no parent)."""
    for record in reversed(records):
        if record.get("module") == module and record.get("addr") == addr:
            return int(record["id"])
    return None


def read_attempts(log_path: Path) -> list[dict]:
    """All attempts, oldest first. A missing log is an empty log.

    Raises ``AttemptError`` on a corrupt line rather than a raw ``JSONDecodeError``, so callers
    (and the CLI) can report it cleanly.
    """
    log_path = Path(log_path)
    if not log_path.exists():
        return []
    records = []
    for lineno, line in enumerate(log_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise AttemptError(f"{log_path}:{lineno}: corrupt attempt log: {e}") from e
    return records


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- the store ------------------------------------------------------------------------

def append(store_dir: Path, record: dict, candidate_text: str | None = None, *,
           now: str | None = None) -> dict:
    """Append one attempt; assign its ``id``/``parent``/``timestamp``; write its candidate.

    ``record`` must carry ``module`` and ``addr``. The parent defaults to the previous attempt
    for the same entry. Returns the stored record (with the assigned fields).
    """
    store_dir = Path(store_dir)
    log_path = store_dir / "log.jsonl"
    records = read_attempts(log_path)

    module, addr = record.get("module"), record.get("addr")
    if not module or addr is None:
        raise AttemptError(f"attempt record missing module/addr: {record!r}")
    attempt_id = next_id(records)

    stored = dict(record)
    stored.setdefault("parent", parent_for(records, module, addr))
    stored["id"] = attempt_id
    stored.setdefault("timestamp", now or utc_now())

    if candidate_text is not None:
        rel = candidate_relpath(module, addr, attempt_id)
        blob = store_dir / rel
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_text(candidate_text)
        stored["candidate"] = rel.as_posix()

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as fh:
        fh.write(json.dumps(stored, sort_keys=True) + "\n")
    return stored


def latest_for(log_path: Path, module: str, addr: str) -> dict | None:
    """The most recent attempt for one entry, or ``None``."""
    for record in reversed(read_attempts(log_path)):
        if record.get("module") == module and record.get("addr") == addr:
            return record
    return None


# --- CLI ------------------------------------------------------------------------------

def _summarize(records: list[dict]) -> list[tuple[str, str, int, int]]:
    """``(module, addr, attempts, matches)`` per entry, in first-seen order."""
    order: list[tuple[str, str]] = []
    counts: dict[tuple[str, str], list[int]] = {}
    for record in records:
        key = (record["module"], record["addr"])
        if key not in counts:
            counts[key] = [0, 0]
            order.append(key)
        counts[key][0] += 1
        counts[key][1] += record.get("outcome") == "match"
    return [(m, a, counts[(m, a)][0], counts[(m, a)][1]) for m, a in order]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", type=Path, default=DEFAULT_STORE)
    ap.add_argument("--module", default=None)
    ap.add_argument("--entry", default=None, help="restrict to one ledger address")
    args = ap.parse_args(argv)

    try:
        records = read_attempts(args.store / "log.jsonl")
    except AttemptError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.module:
        records = [r for r in records if r.get("module") == args.module]
    if args.entry:
        addr = args.entry.lower().removeprefix("0x").zfill(8)
        records = [r for r in records if r.get("addr") == addr]

    if not records:
        print("no attempts recorded")
        return 0
    print(f"{len(records)} attempt(s) across {len({(r['module'], r['addr']) for r in records})} "
          f"entry(ies)")
    for module, addr, attempts, matches in _summarize(records):
        print(f"  {module} {addr}  attempts={attempts}  matches={matches}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
