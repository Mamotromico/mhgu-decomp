"""Decompress a Nintendo Switch NSO executable (pure Python, no dependencies).

MHGU's ``main`` is an ``NSO0`` image whose ``.text``/``.rodata``/``.data`` sections are
LZ4-compressed. This tool parses the NSO header and writes the *decompressed* sections,
which is what any byte-level analysis (diffing, disassembly, matching) must work from.

The devcontainer has neither an ``lz4`` binary nor the ``lz4`` Python module, so the LZ4
block format is implemented here directly. It is the standard LZ4 block layout (not the
LZ4 frame format): a sequence of *token, literals, 2-byte match offset, match* runs,
terminated by a final literal-only sequence.

Usage::

    python3 tools/nso/nso_extract.py <main.nso> <outdir>

Writes ``<outdir>/text.bin``, ``<outdir>/rodata.bin`` and ``<outdir>/data.bin`` and
prints the layout plus a SHA-256 for each section.
"""

from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

# Section descriptors occupy fixed 16-byte slots; the header also stores per-section
# compressed sizes and the BSS size. Offsets confirmed empirically against nstool output.
SECTION_DESCRIPTOR_BASE = 0x10
SECTION_DESCRIPTOR_STRIDE = 0x10
COMPRESSED_SIZE_BASE = 0x60
BSS_SIZE_OFFSET = 0x3C

SECTIONS = ("text", "rodata", "data")


class NsoError(Exception):
    pass


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def read_header(data: bytes) -> dict:
    if data[:4] != b"NSO0":
        raise NsoError(f"not an NSO0 image (magic {data[:4]!r})")
    sections = []
    for i, name in enumerate(SECTIONS):
        base = SECTION_DESCRIPTOR_BASE + SECTION_DESCRIPTOR_STRIDE * i
        sections.append(
            {
                "name": name,
                "file_offset": _u32(data, base + 0x0),
                "memory_offset": _u32(data, base + 0x4),
                "size": _u32(data, base + 0x8),
                "compressed_size": _u32(data, COMPRESSED_SIZE_BASE + 4 * i),
            }
        )
    return {
        "version": _u32(data, 0x04),
        "flags": _u32(data, 0x0C),
        "module_id": data[0x40:0x60].hex(),
        "bss_size": _u32(data, BSS_SIZE_OFFSET),
        "file_size": len(data),
        "sections": sections,
    }


def lz4_block_decompress(src: bytes, expected_size: int | None = None) -> bytes:
    """Decode a raw LZ4 block (as opposed to an LZ4 frame)."""
    out = bytearray()
    i = 0
    n = len(src)
    while i < n:
        token = src[i]
        i += 1

        literal_len = token >> 4
        if literal_len == 15:
            while True:
                extra = src[i]
                i += 1
                literal_len += extra
                if extra != 0xFF:
                    break
        out += src[i : i + literal_len]
        i += literal_len

        # A block may end on a literals-only sequence.
        if i >= n:
            break

        offset = src[i] | (src[i + 1] << 8)
        i += 2
        if offset == 0:
            raise NsoError("invalid LZ4 match offset of 0")

        match_len = token & 0x0F
        if match_len == 15:
            while True:
                extra = src[i]
                i += 1
                match_len += extra
                if extra != 0xFF:
                    break
        match_len += 4

        if offset > len(out):
            raise NsoError("LZ4 match offset points before start of output")
        start = len(out) - offset
        for k in range(match_len):
            out.append(out[start + k])

    if expected_size is not None and len(out) != expected_size:
        raise NsoError(
            f"decompressed {len(out)} bytes, header declared {expected_size}"
        )
    return bytes(out)


def extract(path: Path) -> dict:
    data = path.read_bytes()
    header = read_header(data)

    compressed = bool(header["flags"] & 0x1)
    result = {**header, "path": str(path), "compressed": compressed, "data": {}}

    for section in header["sections"]:
        start = section["file_offset"]
        size = section["size"]
        if compressed:
            blob = data[start : start + section["compressed_size"]]
            payload = lz4_block_decompress(blob, size)
        else:
            payload = data[start : start + size]
        result["data"][section["name"]] = payload
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2

    src = Path(argv[1])
    outdir = Path(argv[2])
    outdir.mkdir(parents=True, exist_ok=True)

    result = extract(src)
    print(f"{src}  (version={result['version']} flags=0x{result['flags']:x} "
          f"compressed={result['compressed']})")
    print(f"  module_id {result['module_id']}")
    print(f"  bss_size  0x{result['bss_size']:x}")
    for section in result["sections"]:
        name = section["name"]
        payload = result["data"][name]
        digest = hashlib.sha256(payload).hexdigest()
        dest = outdir / f"{name}.bin"
        dest.write_bytes(payload)
        print(f"  {name:6} mem=0x{section['memory_offset']:08x} "
              f"size=0x{section['size']:x} sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
