#!/usr/bin/env python3
"""Byte-grounded, coloured instruction diff: real function dump vs. compiled candidate.

Fixed-width ARM A32 => 4 bytes per instruction, so instruction i in the real
disassembly corresponds to bytes [4i, 4i+4) of the real .text, and likewise for
the compiled object. Rows whose 4-byte encodings are equal are shown green, rows
whose encodings differ are red (with the differing bytes).

This compares the *bytes*, not the text, so cosmetic source-syntax differences
(push vs stmdb, blo vs bcc, #104 vs #0x68) do not count as mismatches.

Usage: matchdiff.py <real.asm> <real_text.bin> <off_hex> <nbytes> <compiled.s> <compiled.bin>
"""
import re
import sys

GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def parse_real(path):
    ins = []
    for line in open(path):
        if line.startswith(";;"):
            continue
        m = re.match(r"^\s*[0-9a-fA-F]{8}\s+(\S.*?)\s*$", line)
        if m:
            ins.append(" ".join(m.group(1).split()))
    return ins


def parse_compiled(path):
    ins = []
    for line in open(path):
        if not line.startswith("\t"):
            continue
        body = line[1:].rstrip("\n")
        if body.startswith(".") or not body.strip():
            continue
        ins.append(" ".join(body.split()))
    return ins


def main(argv):
    real_asm, real_bin, off_hex, nb, comp_s, comp_bin = argv[1:7]
    nb = int(nb)
    off = int(off_hex, 16)

    real_ins = parse_real(real_asm)
    comp_ins = parse_compiled(comp_s)
    real_bytes = open(real_bin, "rb").read()[off:off + nb]
    comp_bytes = open(comp_bin, "rb").read()

    w1 = max([len(x) for x in real_ins] + [4])
    w2 = max([len(x) for x in comp_ins] + [4])

    print("%s%s  vs  %s%s" % (BOLD, real_asm, comp_s, RESET))
    print("  %-*s | %-*s" % (w1, "REAL", w2, "COMPILED"))

    nrows = max(len(real_ins), len(comp_ins))
    bad = 0
    for i in range(nrows):
        a = real_bytes[4 * i:4 * i + 4]
        b = comp_bytes[4 * i:4 * i + 4]
        eq = a == b and len(a) == 4
        if not eq:
            bad += 1
        lt = real_ins[i] if i < len(real_ins) else "<none>"
        rt = comp_ins[i] if i < len(comp_ins) else "<none>"
        col = GREEN if eq else RED
        note = ""
        if not eq:
            note = "  %sgot %s want %s%s" % (
                DIM, b.hex(" ") or "--", a.hex(" ") or "--", RESET)
        print("%s %3d  %-*s | %-*s%s" % (col, i, w1, lt, w2, rt, note))

    total = nrows
    print()
    if bad == 0:
        print("%s>>> MATCH%s  (%d/%d instructions, %d bytes)" %
              (GREEN, RESET, total, total, nb))
    else:
        print("%s>>> MISMATCH%s  %d/%d instructions differ" % (RED, RESET, bad, total))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
