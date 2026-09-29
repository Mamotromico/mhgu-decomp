#!/usr/bin/env python3
"""Extract a named ELF section's raw bytes to stdout.

ELF32-LE only (our ARM target). Avoids needing llvm-objcopy, which is absent
from the older prebuilt clang tarballs.

Usage: textof.py <elf> [section]     # default section: .text
"""
import struct
import sys


def main(argv):
    path = argv[1]
    want = argv[2] if len(argv) > 2 else ".text"
    data = open(path, "rb").read()
    assert data[:4] == b"\x7fELF", "not an ELF"
    assert data[4] == 1 and data[5] == 1, "expected ELF32 little-endian"
    e_shoff = struct.unpack_from("<I", data, 0x20)[0]
    e_shentsize = struct.unpack_from("<H", data, 0x2E)[0]
    e_shnum = struct.unpack_from("<H", data, 0x30)[0]
    e_shstrndx = struct.unpack_from("<H", data, 0x32)[0]

    def sh(i):
        base = e_shoff + i * e_shentsize
        name, typ, flags, addr, off, size = struct.unpack_from("<IIIIII", data, base)
        return name, off, size

    _, str_off, str_size = sh(e_shstrndx)
    strtab = data[str_off:str_off + str_size]
    for i in range(e_shnum):
        name_off, off, size = sh(i)
        end = strtab.index(b"\x00", name_off)
        name = strtab[name_off:end].decode()
        if name == want:
            sys.stdout.buffer.write(data[off:off + size])
            return
    sys.exit("section %s not found" % want)


if __name__ == "__main__":
    main(sys.argv)
