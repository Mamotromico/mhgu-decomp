"""Compare the first N bytes of a compiled .text blob against the real function.

Usage: cmpbytes.py <compiled.bin> <real_text.bin> <real_offset_hex> <nbytes>
Prints MATCH or the differing byte positions.
"""
import sys

with open(sys.argv[1], "rb") as f:
    cand = f.read()
with open(sys.argv[2], "rb") as f:
    real = f.read()
off = int(sys.argv[3], 16)
n = int(sys.argv[4])
ref = real[off:off + n]
got = cand[:n]

if len(cand) != n:
    print(f"  LENGTH  got={len(cand)} want={n}  (extra bytes: {cand[n:].hex(' ')})")
if got == ref:
    print(f"  >>> MATCH ({n}/{n})")
else:
    bad = [i for i in range(min(len(got), len(ref))) if got[i] != ref[i]]
    print(f"  >>> MISMATCH {len(bad)}/{n} bytes differ; first at +0x{(bad[0] if bad else -1):x}")
    for i in bad[:16]:
        print(f"      +0x{i:02x}  got {got[i]:02x}  want {ref[i]:02x}")
