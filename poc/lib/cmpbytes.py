#!/usr/bin/env python3
"""Compare the first N bytes of a compiled .text blob against the real function.

Usage: cmpbytes.py <compiled.bin> <real_text.bin> <real_offset_hex> <nbytes>
Prints MATCH or the differing byte positions.
"""
import sys

cand = open(sys.argv[1], "rb").read()
real = open(sys.argv[2], "rb").read()
off = int(sys.argv[3], 16)
n = int(sys.argv[4])
ref = real[off:off + n]
got = cand[:n]

if len(cand) != n:
    print("  LENGTH  got=%d want=%d  (extra bytes: %s)" %
          (len(cand), n, cand[n:].hex(" ")))
if got == ref:
    print("  >>> MATCH (%d/%d)" % (n, n))
else:
    bad = [i for i in range(min(len(got), len(ref))) if got[i] != ref[i]]
    print("  >>> MISMATCH %d/%d bytes differ; first at +0x%x" %
          (len(bad), n, bad[0] if bad else -1))
    for i in bad[:16]:
        print("      +0x%02x  got %02x  want %02x" % (i, got[i], ref[i]))
