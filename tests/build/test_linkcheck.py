"""Tests for the whole-image link check's pure helpers.

The end-to-end pass compiles the tree and compares a 25 MB image; these pin the pieces that
decide *where* a byte lands and *which entry* owns a mismatch. Run with::

    python3 tests/build/test_linkcheck.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

import gotmap
from linkcheck import (
    build_image,
    describe,
    first_mismatch,
    matched_sources,
    owner,
    substitute,
    verified_keys,
)

BASE = 0x60000000


def entry(addr: int, size: int, *, name: str, kind: str = "function",
          verify: str = "match", block: str = ".text") -> dict:
    return {"module": "main", "addr": f"{addr:08x}", "kind": kind, "name": name,
            "block": block, "group": name, "size": str(size), "verify": verify}


class FirstMismatchTests(unittest.TestCase):
    def test_identical_images(self):
        self.assertIsNone(first_mismatch(b"abcd", b"abcd"))

    def test_reports_the_address_of_the_first_difference(self):
        self.assertEqual(first_mismatch(b"abXd", b"abcd", BASE), BASE + 2)

    def test_a_length_difference_is_a_mismatch(self):
        self.assertEqual(first_mismatch(b"abcd", b"abcdef", BASE), BASE + 4)


class SubstituteTests(unittest.TestCase):
    def test_writes_only_the_span(self):
        image = bytearray(b"\x00\x00\x00\x00")
        self.assertEqual(substitute(image, BASE, [(BASE + 1, b"\xaa\xbb")]), [])
        self.assertEqual(bytes(image), b"\x00\xaa\xbb\x00")

    def test_an_out_of_range_span_is_refused(self):
        image = bytearray(4)
        problems = substitute(image, BASE, [(BASE + 3, b"\xaa\xbb")])
        self.assertEqual(len(problems), 1)
        self.assertIn("outside the image", problems[0])
        self.assertEqual(bytes(image), b"\x00\x00\x00\x00")

    def test_overlapping_spans_are_refused(self):
        image = bytearray(8)
        problems = substitute(image, BASE, [(BASE, b"\xaa\xbb\xcc"),
                                            (BASE + 2, b"\xdd")])
        self.assertEqual(len(problems), 1)
        self.assertIn("overlaps", problems[0])
        # The first span landed; the overlapping one did not.
        self.assertEqual(bytes(image), b"\xaa\xbb\xcc\x00\x00\x00\x00\x00")


class OwnerTests(unittest.TestCase):
    ENTRIES = [entry(BASE, 4, name="func_60000000"),
               entry(BASE + 4, 8, name="func_60000004")]

    def test_finds_the_partition(self):
        self.assertEqual(owner(BASE + 5, self.ENTRIES)["name"], "func_60000004")

    def test_below_the_first_entry_is_none(self):
        self.assertIsNone(owner(BASE - 1, self.ENTRIES))

    def test_a_gap_has_no_owner(self):
        entries = [entry(BASE, 4, name="func_60000000"),
                   entry(BASE + 8, 4, name="func_60000008")]
        self.assertIsNone(owner(BASE + 5, entries))

    def test_describe_names_the_entry_and_offset(self):
        self.assertIn("func_60000004", describe(BASE + 6, self.ENTRIES))


class BuildImageTests(unittest.TestCase):
    """The image starts as the original and contributions land at their addresses."""

    def image(self) -> gotmap.Image:
        return gotmap.Image({"text": (BASE, b"\x10\x11\x12\x13"),
                             "data": (BASE + 0x100, b"\x20\x21")})

    def test_without_contributions_it_is_the_original(self):
        image, problems = build_image(self.image(), [])
        self.assertEqual(problems, [])
        self.assertEqual(bytes(image), b"\x10\x11\x12\x13" + b"\x00" * 0xFC + b"\x20\x21")

    def test_a_contribution_replaces_its_bytes(self):
        image, _ = build_image(self.image(), [(BASE + 1, b"\xaa\xbb")])
        self.assertEqual(bytes(image)[:6], b"\x10\xaa\xbb\x13\x00\x00")

    def test_a_wrong_contribution_is_a_mismatch(self):
        reference, _ = build_image(self.image(), [])
        candidate, _ = build_image(self.image(), [(BASE, b"\xff\xff\xff\xff")])
        self.assertEqual(first_mismatch(candidate, reference, BASE), BASE)


class VerifiedKeysTests(unittest.TestCase):
    """Which contributions the image actually reproduces (the Linked metric's input)."""

    def test_only_reproduced_contributions_are_linked(self):
        reference = b"\x01\x02\x03\x04"
        candidate = bytearray(reference)
        candidate[0] ^= 0xFF                     # the first entry's byte is wrong
        contributions = [({"module": "main", "addr": "60000000"}, BASE, b"\x01\x02"),
                         ({"module": "main", "addr": "60000002"}, BASE + 2, b"\x03\x04")]
        self.assertEqual(verified_keys(contributions, bytes(candidate), reference, BASE),
                         ["main:60000002"])

    def test_an_identical_image_links_every_contribution(self):
        reference = b"\x01\x02"
        contributions = [({"module": "main", "addr": "60000000"}, BASE, b"\x01\x02")]
        self.assertEqual(verified_keys(contributions, reference, reference, BASE),
                         ["main:60000000"])


class MatchedSourcesTests(unittest.TestCase):
    def test_only_matched_functions_with_a_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "main").mkdir()
            (root / "main" / "func_60000000.cpp").write_text("x")
            entries = [entry(BASE, 4, name="func_60000000"),
                       entry(BASE + 4, 4, name="func_60000004"),
                       entry(BASE + 8, 4, name="func_60000008", verify="none")]
            found = matched_sources(entries, root)
            self.assertEqual([e["name"] for e in found], ["func_60000000"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
