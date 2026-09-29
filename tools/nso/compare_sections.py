#!/usr/bin/env python3
"""Summarise the byte-level difference between two binary sections.

Naive byte-for-byte diffing of two ~20 MB images is unhelpful: a single inserted
function shifts everything after it, turning one real change into a "whole tail
differs" result. This tool instead reports the quantities that answer *how* the two
images differ:

* common prefix / suffix lengths — where the changes *start* and *stop*;
* differing-byte count over the overlap — how much actually changed;
* a coarse block map — whether differences are a few localised islands or pervasive.

Usage::

    python3 tools/nso/compare_sections.py <a.bin> <b.bin> [block_size=N]
"""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_BLOCK = 0x1000


def common_prefix(a: bytes, b: bytes) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def common_suffix(a: bytes, b: bytes) -> int:
    n = min(len(a), len(b))
    j = 0
    while j < n and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    return j


def differing_bytes(a: bytes, b: bytes) -> int:
    """Count differing byte positions over the overlapping prefix of the two inputs."""
    n = min(len(a), len(b))
    xor = int.from_bytes(a[:n], "big") ^ int.from_bytes(b[:n], "big")
    total = xor.to_bytes((xor.bit_length() + 7) // 8 or 1, "big")
    # `total` may be shorter than n (leading zero bytes); those bytes are equal.
    return n - total.count(0)


def run_blocks(a: bytes, b: bytes, block: int) -> list[tuple[int, int]]:
    """Return [(start, end)] runs of differing blocks over the overlap."""
    n = min(len(a), len(b))
    runs: list[tuple[int, int]] = []
    run_start: int | None = None
    for off in range(0, n, block):
        end = min(off + block, n)
        differs = a[off:end] != b[off:end]
        if differs and run_start is None:
            run_start = off
        elif not differs and run_start is not None:
            runs.append((run_start, off))
            run_start = None
    if run_start is not None:
        runs.append((run_start, n))
    return runs


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("block_size=")]
    block = DEFAULT_BLOCK
    for a in argv[1:]:
        if a.startswith("block_size="):
            block = int(a.split("=", 1)[1], 0)

    if len(args) != 2:
        print(__doc__)
        return 2

    pa, pb = Path(args[0]), Path(args[1])
    a, b = pa.read_bytes(), pb.read_bytes()
    n = min(len(a), len(b))

    print(f"A: {pa}  ({len(a)} bytes / 0x{len(a):x})")
    print(f"B: {pb}  ({len(b)} bytes / 0x{len(b):x})")
    print(f"size delta: {len(b) - len(a):+d} bytes (0x{abs(len(b) - len(a)):x})")

    if a == b:
        print("=> identical")
        return 0

    pre = common_prefix(a, b)
    suf = common_suffix(a, b)
    print(f"common prefix: 0x{pre:x} ({pre} bytes)")
    print(f"common suffix: 0x{suf:x} ({suf} bytes)")

    changed = differing_bytes(a, b)
    print(f"differing bytes over overlap ({n} bytes): {changed} "
          f"({100.0 * changed / n:.2f}%)")

    runs = run_blocks(a, b, block)
    print(f"differing {block:#x}-byte blocks: {len(runs)} "
          f"of {(n + block - 1) // block}")
    print("first 30 differing block runs:")
    for start, end in runs[:30]:
        print(f"  0x{start:08x} .. 0x{end:08x}  ({end - start} bytes)")
    if len(runs) > 30:
        print(f"  ... and {len(runs) - 30} more")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
