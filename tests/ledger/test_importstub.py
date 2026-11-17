"""Tests for the import-stub kind: the encoder, the survey, and the ledger rules around it.

Two properties matter. **Derivation is not decoding**: the body must be recomputed from
``(stub address, GOT slot)`` alone and only then compared with the reference — a test that
fed the reference in would prove nothing. And **the kind is honest**: a stub must leave the
denominator, carry ``gate=link`` and nothing else, and be reported in its own bucket.

Pure functions and temp files — no clang, no NSO, no network. Run with::

    python3 tests/ledger/test_importstub.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

LEDGER_TOOLS = Path(__file__).resolve().parents[2] / "tools" / "ledger"
sys.path.insert(0, str(LEDGER_TOOLS))

import importstub  # noqa: E402
from ledgerlib import (  # noqa: E402
    GATE_VALUES,
    KINDS,
    LEDGER_COLUMNS,
    built_stub,
    counted,
    included,
    matched_counts,
)
from validate import validate  # noqa: E402

HEADER = "\t".join(LEDGER_COLUMNS)

# A real stub and the GOT slot it jumps through (``gotmap.py --stub 0x613f18d0``).
REAL_STUB = 0x613F18D0
REAL_SLOT = 0x61838934
REAL_BODY = bytes.fromhex("04c68fe247ca8ce25cf0bce5")


def stub_row(addr: str = "613f18d0", **over) -> str:
    base = {
        "module": "main", "addr": addr, "kind": "import-stub", "name": f"plt_{addr}",
        "block": ".text", "group": f"plt_{addr}", "size": "12",
        "name_class": "generated", "bind": "", "guess": "0",
        "verify": "match", "gate": "link", "review": "generated", "enroll": "",
    }
    base.update(over)
    return "\t".join(base[c] for c in LEDGER_COLUMNS)


def func_row(addr: str = "60000000", **over) -> str:
    base = {
        "module": "main", "addr": addr, "kind": "function", "name": f"func_{addr}",
        "block": ".text", "group": f"func_{addr}", "size": "4",
        "name_class": "generated", "bind": "", "guess": "0",
        "verify": "none", "gate": "", "review": "generated", "enroll": "rombytes",
    }
    base.update(over)
    return "\t".join(base[c] for c in LEDGER_COLUMNS)


class EncoderTests(unittest.TestCase):
    def test_every_encoding_of_the_page_step_is_offered(self):
        # 2^22 has several A32 forms; which one the linker chose is not the encoder's guess.
        forms = importstub.imm8_rot(0x400000)
        self.assertIn(0x604, forms)   # 4 ROR 12 — the form this image uses
        self.assertIn(0x501, forms)   # 1 ROR 10 — the same value

    def test_a_real_stub_is_rederived_from_its_slot(self):
        self.assertIn(REAL_BODY, importstub.encodings(REAL_STUB, REAL_SLOT))

    def test_a_wrong_slot_is_not_reproduced(self):
        self.assertNotIn(REAL_BODY, importstub.encodings(REAL_STUB, REAL_SLOT + 4))

    def test_the_candidates_reach_exactly_the_requested_slot(self):
        def decode(word: int) -> int:
            """The modified-immediate value of an A32 data-processing word."""
            imm12 = word & 0xFFF
            rot, imm8 = (imm12 >> 8) & 0xF, imm12 & 0xFF
            shift = 2 * rot
            if not shift:
                return imm8
            return ((imm8 >> shift) | (imm8 << (32 - shift))) & 0xFFFFFFFF

        candidates = importstub.encodings(REAL_STUB, REAL_SLOT)
        self.assertTrue(candidates)
        for body in candidates:
            w0, w1, w2 = (int.from_bytes(body[i:i + 4], "little") for i in (0, 4, 8))
            r12 = (REAL_STUB + 8 + decode(w0) + decode(w1)) & 0xFFFFFFFF
            self.assertEqual(len(body), 12)
            self.assertEqual((r12 + (w2 & 0xFFF)) & 0xFFFFFFFF, REAL_SLOT)

    def test_imm8_rot_rejects_an_unencodable_value(self):
        self.assertEqual(importstub.imm8_rot(0x1234), [])


class SurveyTests(unittest.TestCase):
    """``survey`` classifies from the bytes and the GOT map, not from the ledger's claim."""

    def setUp(self):
        # The real stub body sits at its real address, so the derivation is the real one.
        off = REAL_STUB - 0x60000000
        self.text = bytearray(off + 16)
        self.text[off:off + 12] = REAL_BODY
        self.addr = f"{REAL_STUB:08x}"

    def entry(self, **over):
        base = {"addr": self.addr, "kind": "function", "size": "12",
                "verify": "none", "gate": ""}
        base.update(over)
        return base

    def test_an_untyped_stub_is_derived(self):
        recs = importstub.survey([self.entry()], bytes(self.text),
                                 {REAL_STUB: REAL_SLOT})
        self.assertEqual([r["status"] for r in recs], ["derived"])

    def test_a_stub_missing_from_the_got_map_is_reported(self):
        recs = importstub.survey([self.entry()], bytes(self.text), {})
        self.assertEqual([r["status"] for r in recs], ["not-in-gotmap"])

    def test_a_typed_row_that_is_not_a_stub_is_reported(self):
        text = b"\x1e\xff\x2f\xe1" + b"\x00" * 12
        recs = importstub.survey([self.entry(kind="import-stub")], text,
                                 {REAL_STUB: REAL_SLOT})
        self.assertEqual([r["status"] for r in recs], ["typed-not-stub"])

    def test_a_longer_row_that_starts_with_the_idiom_is_ignored(self):
        recs = importstub.survey([self.entry(size="16")], bytes(self.text),
                                 {REAL_STUB: REAL_SLOT})
        self.assertEqual(recs, [])

    def test_a_plain_function_is_ignored(self):
        text = b"\x1e\xff\x2f\xe1" + b"\x00" * 12
        recs = importstub.survey([self.entry(addr="60000000")], text, {})
        self.assertEqual(recs, [])


class LedgerRuleTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def ledger(self, rows: list[str]) -> Path:
        p = self.tmp / "ledger.tsv"
        p.write_text(HEADER + "\n" + "".join(r + "\n" for r in rows))
        return p

    def test_the_kind_and_gate_exist(self):
        self.assertIn("import-stub", KINDS)
        self.assertIn("link", GATE_VALUES)

    def test_a_stub_leaves_the_denominator(self):
        e = {"kind": "import-stub", "size": "12", "verify": "match", "gate": "link"}
        self.assertFalse(included(e))
        self.assertFalse(counted(e))
        self.assertTrue(built_stub(e))

    def test_a_decompiled_row_is_not_a_built_stub(self):
        e = {"kind": "function", "size": "4", "verify": "match", "gate": "raw"}
        self.assertTrue(counted(e))
        self.assertFalse(built_stub(e))

    def test_the_counts_keep_stubs_separate(self):
        entries = [
            {"kind": "function", "size": "4", "verify": "match", "gate": "raw"},
            {"kind": "import-stub", "size": "12", "verify": "match", "gate": "link"},
            {"kind": "import-stub", "size": "12", "verify": "none", "gate": ""},
        ]
        counts = matched_counts(entries)
        self.assertEqual(counts["counted"], 1)
        self.assertEqual(counts["decompiled"], 1)
        self.assertEqual(counts["import_stubs"], 2)
        self.assertEqual(counts["import_stubs_built"], 1)

    def test_a_well_formed_stub_validates(self):
        self.assertEqual(validate(self.ledger([stub_row()]), None), [])

    def test_a_stub_must_not_be_enrolled(self):
        errors = validate(self.ledger([stub_row(enroll="rombytes")]), None)
        self.assertTrue(any("import-stub must have empty enroll" in e for e in errors))

    def test_a_stub_must_be_named_plt(self):
        errors = validate(self.ledger([stub_row(name="func_613f18d0")]), None)
        self.assertTrue(any("func_ name on kind 'import-stub'" in e for e in errors))

    def test_the_link_gate_is_reserved_for_stubs(self):
        errors = validate(self.ledger([func_row(verify="match", gate="link")]), None)
        self.assertTrue(any("only import-stub" in e for e in errors))

    def test_a_stub_cannot_borrow_another_provenance(self):
        errors = validate(self.ledger([stub_row(gate="raw")]), None)
        self.assertTrue(any("must have gate='' or 'link'" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
