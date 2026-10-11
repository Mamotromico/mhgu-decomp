"""Tests for the shape report's selection/histogramming (`gather`).

Uses a tiny synthetic ``.text`` so it is pure and fast — no ledger, no binary. Run with::

    python3 tests/ledger/test_shape_report.py
"""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))

from shape_report import gather
from shapes import render_sig


def word(value: int) -> bytes:
    return struct.pack("<I", value)


# 0x60000000: `add r0, r0, r1; bx lr`  — a leaf no current template covers.
# 0x60000008: `bx lr`                    — the void-return template's shape.
_TEXT = (word(0xE0800001) + word(0xE12FFF1E)   # add r0,r0,r1; bx lr   (8 bytes)
         + word(0xE12FFF1E))                    # bx lr                 (4 bytes)

_ENTRIES = [
    {"kind": "function", "verify": "none", "addr": "60000000", "size": "8", "name": "func_a"},
    {"kind": "function", "verify": "none", "addr": "60000008", "size": "4", "name": "func_b"},
]
_SIZES = {"60000000": 8, "60000008": 4}


class GatherTests(unittest.TestCase):
    def test_excludes_template_covered_shapes_by_default(self):
        sigs, examples, stats = gather(_ENTRIES, _TEXT, _SIZES, [], 0, False)
        self.assertEqual(dict(sigs), {("add r0,r0,r1", "bx lr"): 1})
        self.assertEqual(stats["covered"], 1)
        self.assertEqual(examples[("add r0,r0,r1", "bx lr")], [("60000000", 8)])

    def test_includes_covered_shapes_on_request(self):
        sigs, _, _ = gather(_ENTRIES, _TEXT, _SIZES, [], 0, True)
        self.assertIn(("bx lr",), sigs)
        self.assertEqual(sigs[("bx lr",)], 1)

    def test_counts_pending_and_tiers(self):
        _, _, stats = gather(_ENTRIES, _TEXT, _SIZES, [], 0, False)
        self.assertEqual(stats["pending"], 2)
        self.assertEqual(stats["tier0"], 2)
        self.assertEqual(stats["in_tier"], 2)

    def test_non_function_entries_are_ignored(self):
        entries = _ENTRIES + [{"kind": "data", "verify": "none", "addr": "60000000",
                               "size": "4", "name": "D_a"}]
        _, _, stats = gather(entries, _TEXT, _SIZES, [], 0, False)
        self.assertEqual(stats["pending"], 2)

    def test_render_sig_is_stable(self):
        sigs, _, _ = gather(_ENTRIES, _TEXT, _SIZES, [], 0, False)
        (sig,) = sigs
        self.assertEqual(render_sig(sig), "add r0,r0,r1; bx lr")


if __name__ == "__main__":
    unittest.main(verbosity=2)
