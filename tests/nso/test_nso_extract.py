"""Tests for the NSO header parser and the LZ4 block decoder. No binary needed. Run with::

    python3 tests/nso/test_nso_extract.py
"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "nso"))

from nso_extract import (
    COMPRESSED_SIZE_BASE,
    NsoError,
    extract,
    lz4_block_decompress,
    main,
    read_header,
)

PDATA = b"ABCD"  # 4 common literals


def lz4_literals_only(data: bytes) -> bytes:
    """Encode ``data`` as a single literals-only LZ4 block (a valid block end)."""
    length = len(data)
    out = bytearray()
    if length < 15:
        out.append(length << 4)
    else:
        out.append(0xF0)
        rest = length - 15
        while rest >= 255:
            out.append(255)
            rest -= 255
        out.append(rest)
    return bytes(out) + data


def build_image(payloads: list[bytes], *, compressed: bool = False,
                sizes: list[int] | None = None) -> bytes:
    """Assemble a synthetic 3-section NSO0 image (text, rodata, data)."""
    header = bytearray(0x100)
    header[0:4] = b"NSO0"
    struct.pack_into("<I", header, 0x04, 0)          # version
    struct.pack_into("<I", header, 0x0C, 1 if compressed else 0)
    struct.pack_into("<I", header, 0x3C, 0xB000)     # bss size
    header[0x40:0x60] = bytes(range(0x20))           # module id
    offset = 0x100
    body = bytearray()
    for i, blob in enumerate(payloads):
        base = 0x10 + 0x10 * i
        struct.pack_into("<I", header, base + 0x0, offset)
        struct.pack_into("<I", header, base + 0x4, 0x60000000 + i * 0x1000)
        declared = len(blob) if sizes is None else sizes[i]
        struct.pack_into("<I", header, base + 0x8, declared)
        struct.pack_into("<I", header, COMPRESSED_SIZE_BASE + 4 * i, len(blob))
        body += blob
        offset += len(blob)
    return bytes(header) + bytes(body)


class Lz4Tests(unittest.TestCase):
    def test_literals_only_short(self):
        self.assertEqual(lz4_block_decompress(lz4_literals_only(b"hello")), b"hello")

    def test_literals_only_extended_length(self):
        data = bytes(range(256)) * 2  # 512 bytes -> extended length encoding
        self.assertEqual(lz4_block_decompress(lz4_literals_only(data)), data)

    def test_match_copies_from_output(self):
        # token(0x40): 4 literals, match length 0 + 4; literals "ABCD"; offset 4 -> "ABCDABCD".
        block = bytes([0x40]) + PDATA + b"\x04\x00" + b"\x00"
        self.assertEqual(lz4_block_decompress(block), b"ABCDABCD")

    def test_declared_size_mismatch_raises(self):
        with self.assertRaises(NsoError):
            lz4_block_decompress(lz4_literals_only(b"abc"), expected_size=4)

    def test_zero_offset_raises(self):
        block = bytes([0x10]) + b"a" + b"\x00\x00"
        with self.assertRaises(NsoError):
            lz4_block_decompress(block)

    def test_truncated_literals_raise(self):
        # token declares 5 literals but only 2 bytes follow
        with self.assertRaises(NsoError):
            lz4_block_decompress(bytes([0x50]) + b"ab")

    def test_truncated_extended_length_raises(self):
        with self.assertRaises(NsoError):
            lz4_block_decompress(bytes([0xF0]))  # says "15+", then EOF


class ReadHeaderTests(unittest.TestCase):
    def test_rejects_non_nso(self):
        with self.assertRaises(NsoError):
            read_header(b"MZ\x00\x00" + b"\x00" * 0x200)

    def test_rejects_truncated_header(self):
        with self.assertRaises(NsoError):
            read_header(b"NSO0" + b"\x00" * 0x10)

    def test_reads_sections_and_metadata(self):
        img = build_image([b"AAA", b"BB", b"C"])
        header = read_header(img)
        self.assertEqual(header["bss_size"], 0xB000)
        self.assertEqual([s["name"] for s in header["sections"]],
                         ["text", "rodata", "data"])
        self.assertEqual(header["sections"][0]["size"], 3)


class ExtractTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def write(self, data: bytes) -> Path:
        path = self.tmp / "main.nso"
        path.write_bytes(data)
        return path

    def test_uncompressed_round_trip(self):
        path = self.write(build_image([b"AAA", b"BB", b"C"]))
        result = extract(path)
        self.assertFalse(result["compressed"])
        self.assertEqual(result["data"]["text"], b"AAA")
        self.assertEqual(result["data"]["rodata"], b"BB")
        self.assertEqual(result["data"]["data"], b"C")

    def test_compressed_section_decompresses(self):
        blob = lz4_literals_only(b"hello world")
        path = self.write(build_image([blob, b"", b""], compressed=True,
                                      sizes=[len(b"hello world"), 0, 0]))
        result = extract(path)
        self.assertTrue(result["compressed"])
        self.assertEqual(result["data"]["text"], b"hello world")

    def test_section_past_end_of_file_raises(self):
        img = bytearray(build_image([b"AAA", b"BB", b"C"]))
        struct.pack_into("<I", img, 0x10 + 0x8, 0x10000)  # text size absurdly large
        with self.assertRaises(NsoError):
            extract(self.write(bytes(img)))

    def test_cli_writes_sections(self):
        path = self.write(build_image([b"AAA", b"BB", b"C"]))
        out = self.tmp / "out"
        self.assertEqual(main([str(path), str(out)]), 0)
        self.assertEqual((out / "text.bin").read_bytes(), b"AAA")
        self.assertEqual((out / "data.bin").read_bytes(), b"C")

    def test_cli_missing_file_returns_one(self):
        self.assertEqual(main([str(self.tmp / "nope.nso"), str(self.tmp / "out")]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
