"""Tests for the section difference summary: prefix/suffix, differing count, block runs, CLI.

    python3 tests/nso/test_compare_sections.py
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "nso"))

from compare_sections import (
    common_prefix,
    common_suffix,
    differing_bytes,
    main,
    run_blocks,
)


class CommonTests(unittest.TestCase):
    def test_prefix(self):
        self.assertEqual(common_prefix(b"abcXYZ", b"abcQ"), 3)

    def test_suffix(self):
        self.assertEqual(common_suffix(b"XYZabc", b"Qabc"), 3)

    def test_empty(self):
        self.assertEqual(common_suffix(b"", b""), 0)
        self.assertEqual(common_prefix(b"", b"x"), 0)


class DifferingBytesTests(unittest.TestCase):
    def test_empty_overlap_is_zero(self):
        self.assertEqual(differing_bytes(b"", b"x"), 0)
        self.assertEqual(differing_bytes(b"", b""), 0)

    def test_identical_is_zero(self):
        self.assertEqual(differing_bytes(b"abcd", b"abcd"), 0)

    def test_leading_equal_bytes_are_not_counted(self):
        # Regression: the previous minimal-length XOR encoding overcounted here.
        self.assertEqual(differing_bytes(b"\x00\x01", b"\x00\x02"), 1)

    def test_all_differ(self):
        self.assertEqual(differing_bytes(b"aa", b"bb"), 2)

    def test_only_overlap_is_compared(self):
        self.assertEqual(differing_bytes(b"abcd", b"abXYzz"), 2)


class RunBlocksTests(unittest.TestCase):
    def test_single_run(self):
        a = b"\x00" * 16
        b = b"\x00" * 4 + b"\xff" * 4 + b"\x00" * 8
        self.assertEqual(run_blocks(a, b, 4), [(4, 8)])

    def test_trailing_run_reaches_overlap_end(self):
        a = b"\x00" * 8
        b = b"\x00" * 4 + b"\xff" * 4
        self.assertEqual(run_blocks(a, b, 4), [(4, 8)])

    def test_no_runs_when_identical(self):
        self.assertEqual(run_blocks(b"abcd", b"abcd", 4), [])


class MainTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def write(self, name: str, data: bytes) -> Path:
        path = self.tmp / name
        path.write_bytes(data)
        return path

    def run_main(self, argv: list[str]) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = main(argv)
        return rc, out.getvalue()

    def test_identical(self):
        a = self.write("a.bin", b"same bytes")
        b = self.write("b.bin", b"same bytes")
        rc, out = self.run_main([str(a), str(b)])
        self.assertEqual(rc, 0)
        self.assertIn("=> identical", out)

    def test_space_separated_block_size_and_differing_report(self):
        a = self.write("a.bin", b"\x00" * 16)
        b = self.write("b.bin", b"\x00" * 4 + b"\xff" * 4 + b"\x00" * 8)
        rc, out = self.run_main([str(a), str(b), "--block-size", "4"])
        self.assertEqual(rc, 0)
        self.assertIn("differing bytes over overlap", out)
        self.assertIn("differing 0x4-byte blocks", out)

    def test_missing_file_returns_one(self):
        rc, _ = self.run_main([str(self.tmp / "nope"), str(self.tmp / "nope2")])
        self.assertEqual(rc, 1)

    def test_zero_block_size_is_a_usage_error(self):
        a = self.write("a.bin", b"x")
        b = self.write("b.bin", b"y")
        with self.assertRaises(SystemExit) as ctx:
            self.run_main([str(a), str(b), "--block-size", "0"])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
