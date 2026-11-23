"""The attempt log: an append-only, parent-linked record of every reconstruction attempt.

Every attempt is kept — a near miss is evidence, not waste (``AGENTS.md``) — under the
git-ignored ``baserom/work/attempts/``:

::

    baserom/work/attempts/
      log.jsonl                 # append-only; one JSON object per attempt
      index.json                # derived per-entry index over the log (see below)
      <module>/<addr>/001.cpp   # the candidate that attempt produced

Two properties matter:

* **Append-only.** Records are never rewritten. The log *is* the history; the near-miss bank
  (``nearmiss.py``) is the derived best-of view.
* **Parent-linked.** Each attempt points at the previous attempt for the same ``(module,
  addr)`` (``parent``), so retries form a tree — an attempt with no parent is the first for
  that entry. ``append`` computes the parent automatically unless one is supplied.

The incremental index
---------------------
The log grows monotonically (tens of thousands of records), and the hot operations only
ever need per-entry answers: *how many attempts does this entry have*, *what is its latest
attempt*, *fetch record N*. Answering those by rereading the whole log makes every append
and every lookup O(history). ``index.json`` is a derived cache of exactly those answers::

    {
      "version": 1,
      "log":  {"size": <bytes>, "mtime_ns": <int>, "lines": <n>},   # fingerprint
      "next_id": 42,                                                # global max id + 1
      "entries": {"main/601a72e4": {"count": 3, "last_id": 41, "last_offset": 1234}},
      "id_offsets": {"41": 1234}      # attempt id -> byte offset, for direct re-reads
    }

The log stays the sole authority. The index is keyed by the log's fingerprint
(``size`` + ``mtime_ns``, the convention the gotmap/refcache caches use) plus an index
schema version; any mismatch, corrupt sidecar, or truncated/replaced log rebuilds it from
one full scan, and the rebuild is written atomically (temp file + rename). A crash between
appending a log line and saving the index is repaired the same way: the fingerprint no
longer matches, so the next operation rebuilds. An index answer is never trusted when the
fingerprint disagrees — it is rebuilt instead. Full-history consumers (``regate_candidates``
iterates every record) keep reading the log sequentially; indexing cannot speed up a query
that consumes everything.

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
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_STORE = REPO / "baserom" / "work" / "attempts"

LOG_NAME = "log.jsonl"
INDEX_NAME = "index.json"
# Bump when the index schema changes (the extractor-version half of the cache key).
INDEX_VERSION = 1


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


# --- the incremental index ------------------------------------------------------------
#
# ``index.json`` is a derived, self-healing cache over the append-only log: per-entry
# counts/latest, a global next id, and id -> byte-offset for direct re-reads. The log is
# the sole authority; the index is rebuilt from it whenever their fingerprints disagree,
# so an interrupted write or a truncated log costs one rebuild and can never serve a
# stale answer. A small in-process cache (keyed by the log's size+mtime, checked with a
# cheap stat) keeps loops of lookups from re-reading the sidecar each call.

_CACHE: dict[str, tuple[int, int, dict]] = {}   # store dir -> (log size, mtime_ns, index)


def _entry_key(module: str, addr: str) -> str:
    return f"{module}/{addr}"


def build_index(log_path: Path) -> dict:
    """Scan ``log_path`` once into a fresh index (the slow path every consumer shares).

    Raises :class:`AttemptError` on a corrupt line — the same fail-closed contract as
    :func:`read_attempts`: a damaged log is reported, never silently indexed.
    """
    log_path = Path(log_path)
    index = {"version": INDEX_VERSION,
             "log": {"size": 0, "mtime_ns": 0, "lines": 0},
             "next_id": 1, "entries": {}, "id_offsets": {}}
    if not log_path.exists():
        return index
    entries, id_offsets = index["entries"], index["id_offsets"]
    offset, lines, next_id = 0, 0, 1
    with log_path.open("rb") as fh:
        for lineno, raw in enumerate(fh, start=1):
            if not raw.strip():
                offset += len(raw)
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as e:
                raise AttemptError(f"{log_path}:{lineno}: corrupt attempt log: {e}") from e
            rid = int(record.get("id") or 0)
            next_id = max(next_id, rid + 1)
            if rid:
                id_offsets[str(rid)] = offset
            if record.get("module") is not None and record.get("addr") is not None:
                key = _entry_key(record["module"], record["addr"])
                entry = entries.setdefault(key, {"count": 0, "last_id": 0, "last_offset": 0})
                entry["count"] += 1
                entry["last_id"] = rid
                entry["last_offset"] = offset
            offset += len(raw)
            lines += 1
    stat = log_path.stat()
    index["log"] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "lines": lines}
    index["next_id"] = next_id
    return index


def save_index(store_dir: Path, index: dict) -> None:
    """Persist the index atomically (temp file + rename) so a crash mid-save leaves the
    previous index — or none — in place, never a half-written one."""
    store_dir = Path(store_dir)
    store_dir.mkdir(parents=True, exist_ok=True)
    tmp = store_dir / (INDEX_NAME + ".tmp")
    tmp.write_text(json.dumps(index, indent=1, sort_keys=True) + "\n")
    os.replace(tmp, store_dir / INDEX_NAME)


def _index_serves(index: dict, log_path: Path) -> bool:
    """Whether the index's fingerprint matches the log it claims to describe."""
    try:
        stat = Path(log_path).stat()
    except OSError:
        return False
    info = index.get("log") or {}
    return (index.get("version") == INDEX_VERSION
            and info.get("size") == stat.st_size
            and info.get("mtime_ns") == stat.st_mtime_ns)


def load_index(store_dir: Path) -> dict:
    """The current index: served from memory/disk when its fingerprint matches the log,
    rebuilt from a full scan (and re-saved) otherwise.

    Corrupt sidecar, version mismatch, an externally grown/shrunk/replaced log — all
    land on the same rebuild path. The in-process cache is keyed by the log's
    ``size``/``mtime_ns`` and validated with one ``stat`` per call, so a loop of
    thousands of lookups pays one sidecar read, and an external log edit between calls
    is still noticed."""
    store_dir = Path(store_dir)
    log_path = store_dir / LOG_NAME
    key = str(store_dir.resolve())
    try:
        stat = log_path.stat()
    except OSError:
        stat = None
    if stat is not None:
        cached = _CACHE.get(key)
        if cached is not None and cached[0] == stat.st_size and cached[1] == stat.st_mtime_ns:
            return cached[2]
    index = None
    idx_path = store_dir / INDEX_NAME
    if idx_path.exists():
        try:
            parsed = json.loads(idx_path.read_text())
        except (json.JSONDecodeError, OSError):
            parsed = None
        if isinstance(parsed, dict) and _index_serves(parsed, log_path):
            index = parsed
    if index is None:
        index = build_index(log_path)
        if stat is not None:
            # No log -> nothing to index; don't create a store that may not even be
            # writable (a missing log reads as an empty index, as it always did).
            save_index(store_dir, index)
    if stat is not None:
        _CACHE[key] = (stat.st_size, stat.st_mtime_ns, index)
    return index


def _cache_index(store_dir: Path, index: dict) -> None:
    """Refresh the in-process cache entry after ``append`` mutates the index."""
    log_path = Path(store_dir) / LOG_NAME
    try:
        stat = log_path.stat()
    except OSError:
        return
    _CACHE[str(Path(store_dir).resolve())] = (stat.st_size, stat.st_mtime_ns, index)


def record_at(log_path: Path, offset: int) -> dict:
    """Re-read exactly one record by its byte offset (one seek, one line)."""
    log_path = Path(log_path)
    size = log_path.stat().st_size
    if offset < 0 or offset >= size:
        raise AttemptError(f"attempt index offset {offset} is outside {log_path} "
                           f"({size} B); the index is stale — rebuild it")
    with log_path.open("rb") as fh:
        fh.seek(offset)
        raw = fh.readline()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise AttemptError(f"{log_path}: corrupt record at offset {offset}: {e}") from e


def attempt_counts(store_dir: Path) -> dict[tuple[str, str], int]:
    """``(module, addr) -> attempt count`` straight from the index — no log scan."""
    counts: dict[tuple[str, str], int] = {}
    for key, entry in load_index(store_dir)["entries"].items():
        module, addr = key.split("/", 1)
        counts[(module, addr)] = int(entry["count"])
    return counts


def records_by_id(store_dir: Path, ids) -> dict[int, dict]:
    """The records for ``ids`` (one seek each, single file open), for repair seeding.

    An id the index does not know — or whose offset does not round-trip to a record with
    that id — is omitted rather than guessed at.
    """
    store_dir = Path(store_dir)
    log_path = store_dir / LOG_NAME
    id_set = {int(r) for r in ids if r is not None}
    if not id_set:
        return {}
    offsets = load_index(store_dir)["id_offsets"]
    pending = sorted((int(off), int(rid)) for rid, off in offsets.items()
                     if int(rid) in id_set)
    out: dict[int, dict] = {}
    with log_path.open("rb") as fh:
        for offset, rid in pending:
            fh.seek(offset)
            raw = fh.readline()
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as e:
                raise AttemptError(f"{log_path}: corrupt record at offset {offset}: {e}") from e
            if record.get("id") == rid:
                out[rid] = record
    return out


# --- the store ------------------------------------------------------------------------

def append(store_dir: Path, record: dict, candidate_text: str | None = None, *,
           now: str | None = None) -> dict:
    """Append one attempt; assign its ``id``/``parent``/``timestamp``; write its candidate.

    ``record`` must carry ``module`` and ``addr``. The parent defaults to the previous attempt
    for the same entry (from the index, not a rescan). Returns the stored record (with the
    assigned fields). The authoritative line is appended first; the index is updated and
    saved after, so a crash between the two is repaired by the next load (fingerprint
    mismatch -> rebuild).
    """
    store_dir = Path(store_dir)
    log_path = store_dir / LOG_NAME
    index = load_index(store_dir)

    module, addr = record.get("module"), record.get("addr")
    if not module or addr is None:
        raise AttemptError(f"attempt record missing module/addr: {record!r}")
    attempt_id = int(index["next_id"])

    stored = dict(record)
    key = _entry_key(module, addr)
    last = index["entries"].get(key)
    stored.setdefault("parent", last["last_id"] if last else None)
    stored["id"] = attempt_id
    stored.setdefault("timestamp", now or utc_now())

    if candidate_text is not None:
        rel = candidate_relpath(module, addr, attempt_id)
        blob = store_dir / rel
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_text(candidate_text)
        stored["candidate"] = rel.as_posix()

    offset = log_path.stat().st_size if log_path.exists() else 0
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as fh:
        fh.write(json.dumps(stored, sort_keys=True) + "\n")

    entry = index["entries"].setdefault(key, {"count": 0, "last_id": 0, "last_offset": 0})
    entry["count"] += 1
    entry["last_id"] = attempt_id
    entry["last_offset"] = offset
    index["id_offsets"][str(attempt_id)] = offset
    index["next_id"] = attempt_id + 1
    stat = log_path.stat()
    index["log"] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                    "lines": int(index["log"].get("lines") or 0) + 1}
    save_index(store_dir, index)
    _cache_index(store_dir, index)
    return stored


def latest_for(log_path: Path, module: str, addr: str) -> dict | None:
    """The most recent attempt for one entry, or ``None`` — a one-line seek via the index."""
    log_path = Path(log_path)
    entry = load_index(log_path.parent)["entries"].get(_entry_key(module, addr))
    if entry is None:
        return None
    return record_at(log_path, int(entry["last_offset"]))


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
