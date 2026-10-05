#!/usr/bin/env python3
"""The near-miss bank: the best near-miss per entry, with a strictly-improving upsert.

It is the derived, best-of view over the append-only attempt log (``attempts.py``). Where the
log keeps *every* attempt, the bank keeps only the **closest so far** for each entry — so a
retry that gets worse never destroys the evidence of the retry that got closer
(``docs/llm-harness-design.md`` → *The harness*).

Closeness is a lexicographic pair, **lower is better**::

    closeness = (|candidate_size − body_size|, divergences)

The length error is ranked **first**: a candidate whose body length differs is a structurally
different shape, and its ``diff_count`` is not comparable to a same-length candidate's — a
much shorter, folded body trivially has few differing bytes. Ranking length error first makes
the bank's order agree with the gate's ``body-length`` status. ``divergences`` is the gate's
``diff_count`` over the compared span; both terms come straight from the gate's structured
``--report``, never from the bank re-deriving a comparison (the gate is authoritative).

**The eval pin.** The metric and the compiler pin together determine whether two closeness
numbers are comparable. Both are fingerprinted into ``eval_pin``:

* the metric definition (``METRIC`` below — bump it when the formula changes), and
* ``config/toolchain.json`` (the compiler pin — the whole of ``compiler-identification.md`` is
  evidence that a different compiler makes different bytes).

A record carries the pin it was written under. When the current pin differs, the upsert
**warns** rather than silently comparing incomparable numbers, and treats the old record as
absent (it cannot be compared). This is also what makes a future experiment — e.g. "does a
decompiler draft help?" — trustworthy: A/B it against a pinned eval, not by vibes.

The bank is stored git-ignored at ``baserom/work/nearmiss/bank.json``.

Usage::

    python3 tools/loop/nearmiss.py                 # the bank, closest first
    python3 tools/loop/nearmiss.py --module main
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_BANK = REPO / "baserom" / "work" / "nearmiss" / "bank.json"
DEFAULT_TOOLCHAIN = REPO / "config" / "toolchain.json"

# Bump when the closeness formula changes, so old numbers stop being silently comparable.
METRIC = "closeness/v2"


# --- pure helpers (unit-tested) -------------------------------------------------------

def eval_pin(toolchain_path: Path) -> str:
    """Fingerprint the comparability inputs: the metric definition + the compiler pin."""
    digest = hashlib.sha256()
    digest.update(METRIC.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(Path(toolchain_path).read_bytes())
    return digest.hexdigest()[:16]


def closeness(diff_count: int, cand_len: int, body_len: int) -> list[int]:
    """``(|candidate_size − body_size|, divergences)`` — lower is better.

    Length error ranks ahead of divergences: across different lengths ``diff_count`` is not
    comparable (a folded stub has almost no diverging bytes), so the bank must prefer the
    candidate that at least matches the body length, then the one with fewer divergences.
    """
    return [abs(int(cand_len) - int(body_len)), int(diff_count)]


def key(module: str, addr: str) -> str:
    return f"{module}:{addr}"


def empty_bank() -> dict:
    return {"metric": METRIC, "records": {}}


def load_bank(path: Path) -> dict:
    """Read the bank; a missing file is an empty bank."""
    path = Path(path)
    if not path.exists():
        return empty_bank()
    return json.loads(path.read_text())


def save_bank(path: Path, bank: dict) -> None:
    """Deterministic JSON (stable keys, trailing newline)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bank, indent=2, sort_keys=True) + "\n")


def best(bank: dict, module: str, addr: str, pin: str) -> dict | None:
    """The comparable best record for an entry, or ``None`` (absent, or a different pin)."""
    record = bank.get("records", {}).get(key(module, addr))
    if record is None or record.get("pin") != pin:
        return None
    return record


def upsert(bank: dict, module: str, addr: str, new_closeness: list[int], pin: str,
           now: str | None = None, **extra) -> tuple[dict, dict]:
    """Strictly-improving upsert. Returns ``(bank, result)``.

    ``result`` is ``{"updated": bool, "reason": str, "previous": [...], "warn": str|None}``.
    A higher-or-equal closeness leaves the record untouched; a record written under a different
    pin cannot be compared and is replaced with a warning.
    """
    records = bank.setdefault("records", {})
    existing = records.get(key(module, addr))
    warn = None

    if existing is None:
        reason = "new"
    elif existing.get("pin") != pin:
        reason = "re-pinned"
        warn = (f"eval pin changed for {key(module, addr)}: previous closeness "
                f"{existing.get('closeness')} (pin {existing.get('pin')}) is not comparable "
                f"to the current pin {pin}")
    elif list(new_closeness) < list(existing["closeness"]):
        reason = "improved"
    else:
        return bank, {"updated": False, "reason": "not-improved", "warn": None,
                      "previous": existing.get("closeness")}

    record = {"module": module, "addr": addr, "closeness": list(new_closeness), "pin": pin,
              "updated": now or datetime.now(timezone.utc).isoformat(timespec="seconds")}
    record.update(extra)
    bank["metric"] = METRIC
    records[key(module, addr)] = record
    return bank, {"updated": True, "reason": reason, "warn": warn,
                  "previous": existing.get("closeness") if existing else None}


def record(path: Path, module: str, addr: str, new_closeness: list[int], pin: str, *,
           now: str | None = None, **extra) -> dict:
    """Load the bank, apply the upsert, save if improved, and return the result."""
    bank = load_bank(path)
    if bank.get("metric") not in (None, METRIC):
        bank = empty_bank()  # metric changed: old bank is a different space entirely
    bank, result = upsert(bank, module, addr, new_closeness, pin, now=now, **extra)
    if result["updated"]:
        save_bank(path, bank)
    return result


# --- CLI ------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    ap.add_argument("--module", default=None)
    args = ap.parse_args(argv)

    bank = load_bank(args.bank)
    records = list(bank.get("records", {}).values())
    if args.module:
        records = [r for r in records if r.get("module") == args.module]
    if not records:
        print("near-miss bank is empty")
        return 0
    records.sort(key=lambda r: (list(r["closeness"]), r["module"], r["addr"]))
    print(f"near-miss bank: {len(records)} entry(ies), metric={bank.get('metric')}")
    for r in records:
        delta, div = r["closeness"]
        print(f"  {r['module']} {r['addr']}  divergences={div:<6} len_delta={delta:<4} "
              f"{r.get('name', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
