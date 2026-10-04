#!/usr/bin/env python3
"""Align two binaries that are *mostly* identical but shifted by insertions.

A plain byte-for-byte comparison of two NSO `.text` sections is misleading: the update
adds a handful of bytes in many places, so every byte after the first insertion shows as
"differing" even though the content is unchanged. This tool recovers the real edit
story by walking both inputs and classifying each gap as:

* **match**        — byte-identical run (the content simply shifted),
* **insert**       — bytes present only in B (new code),
* **delete**       — bytes present only in A (removed code),
* **substitute**   — a short in-place change (same-ish location, different bytes).

It is a heuristic resync diff (anchor on a run of ``--min-match`` bytes, prefer the
smallest shift), which is accurate for the "same compiler, small patch" case this is
built for. It is *not* a general-purpose optimal diff.

Usage::

    python3 tools/nso/text_align.py <a.bin> <b.bin> [--min-match N] [--window N]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

MIN_MATCH = 32
WINDOW = 1 << 16
PROGRESS_INTERVAL = 0.5  # seconds between heartbeat lines


def match_len(a: bytes, b: bytes, i: int, j: int) -> int:
    """Length of the identical run starting at a[i] / b[j] (gallop + binary search)."""
    n = min(len(a) - i, len(b) - j)
    lo = 0
    step = 64
    while lo < n and a[i + lo : i + lo + step] == b[j + lo : j + lo + step]:
        lo += step
    hi = min(n, lo + step)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if a[i : i + mid] == b[j : j + mid]:
            lo = mid
        else:
            hi = mid - 1
    return lo


def align(a: bytes, b: bytes, min_match: int, window: int, progress=None,
          progress_interval: float = PROGRESS_INTERVAL) -> list[dict]:
    events: list[dict] = []
    i = j = 0
    na, nb = len(a), len(b)
    start = last_report = time.monotonic()
    while i < na and j < nb:
        if progress is not None:
            now = time.monotonic()
            if now - last_report >= progress_interval:
                last_report = now
                progress(i, na, j, nb, len(events), now - start)
        m = match_len(a, b, i, j)
        if m >= min_match:
            i += m
            j += m
            continue

        # Try a short in-place substitution (same length change).
        probe = min(min_match, na - i, nb - j)
        subst = None
        for d in range(1, 256):
            if i + d + probe > na or j + d + probe > nb:
                break
            if a[i + d : i + d + probe] == b[j + d : j + d + probe]:
                subst = d
                break
        if subst is not None:
            events.append({"type": "substitute", "a": i, "b": j, "len": subst})
            i += subst
            j += subst
            continue

        # Insertion/deletion detection needs a full-length anchor on *both*
        # sides. Near the very end a slice would be shorter than min_match and
        # could match at the current position, producing a zero-length event and
        # an infinite loop, so only probe while enough bytes remain. Every
        # branch below advances i and/or j by at least one byte.
        if na - i >= min_match and nb - j >= min_match:
            # Insertion in B: A's upcoming bytes appear further ahead in B.
            anchor = a[i : i + min_match]
            q = b.find(anchor, j, j + window)
            # Deletion from A: B's upcoming bytes appear further ahead in A.
            anchor_b = b[j : j + min_match]
            p = a.find(anchor_b, i, i + window)

            if q > j and (p <= i or (q - j) <= (p - i)):
                events.append({"type": "insert", "a": i, "b": j, "len": q - j})
                j = q
                continue
            if p > i:
                events.append({"type": "delete", "a": i, "b": j, "len": p - i})
                i = p
                continue

        # Fallback: a genuine in-place byte change (guarantees forward progress).
        events.append({"type": "substitute", "a": i, "b": j, "len": 1})
        i += 1
        j += 1

    if i < na:
        events.append({"type": "delete", "a": i, "b": j, "len": na - i})
    if j < nb:
        events.append({"type": "insert", "a": i, "b": j, "len": nb - j})
    if progress is not None:
        progress(i, na, j, nb, len(events), time.monotonic() - start)
    return events


def _make_progress(label: str):
    """Return a heartbeat callback that rewrites one stderr line while running."""
    tty = sys.stderr.isatty()
    end = "\r" if tty else "\n"

    def report(i: int, na: int, j: int, nb: int, events: int, elapsed: float) -> None:
        pct = 100.0 * i / na if na else 100.0
        rate = i / elapsed if elapsed > 0 else 0.0
        sys.stderr.write(
            f"{end}[{label}] {pct:6.2f}% of A  "
            f"a=0x{i:07x}/{na}  b=0x{j:07x}/{nb}  "
            f"events={events}  elapsed={elapsed:6.1f}s  "
            f"rate={rate / 1024:8.1f} KB/s"
        )
        sys.stderr.flush()

    return report


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    opts = {a.split("=")[0]: a.split("=")[1] for a in argv[1:] if a.startswith("--") and "=" in a}
    min_match = int(opts.get("--min-match", MIN_MATCH))
    window = int(opts.get("--window", WINDOW))
    if len(args) != 2:
        print(__doc__)
        return 2

    a = Path(args[0]).read_bytes()
    b = Path(args[1]).read_bytes()
    print(f"aligning {len(a)} B (A) vs {len(b)} B (B), min-match={min_match} window={window}",
          file=sys.stderr, flush=True)
    events = align(a, b, min_match, window, progress=_make_progress("align"))
    if sys.stderr.isatty():
        sys.stderr.write("\n")

    totals: dict[str, int] = {}
    for e in events:
        totals[e["type"]] = totals.get(e["type"], 0) + e["len"]

    n = min(len(a), len(b))
    changed = totals.get("insert", 0) + totals.get("delete", 0) + totals.get("substitute", 0)
    print(f"A: {args[0]}  ({len(a)} bytes)")
    print(f"B: {args[1]}  ({len(b)} bytes)")
    print(f"identical content: ~{n - changed if changed < n else 0} bytes "
          f"of {n} overlap ({100.0 * max(0, n - changed) / n:.2f}%)")
    for kind in ("insert", "delete", "substitute"):
        print(f"  {kind:11} {totals.get(kind, 0):7d} bytes in {sum(1 for e in events if e['type'] == kind)} regions")

    big = sorted(events, key=lambda e: -e["len"])[:15]
    print("largest change regions (base offset, update offset, length):")
    for e in big:
        print(f"  {e['type']:11} base=0x{e['a']:08x} update=0x{e['b']:08x} len={e['len']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
