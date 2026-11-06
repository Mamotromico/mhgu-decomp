"""Tests for the ledger's shared schema and its line-surgical status write.

The write is what makes ``verify`` + ``gate`` one status update, so these pin the two
properties that matter: only the addressed line changes, and the columns land together.
Pure functions + temp files. Run with::

    python3 tests/ledger/test_ledgerlib.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

from ledgerlib import (
    GATE_VALUES,
    LEDGER_COLUMNS,
    STATUS_DEFAULTS,
    set_field,
    set_fields,
)

HEADER = "\t".join(LEDGER_COLUMNS)


def row(addr: str, verify: str = "none", gate: str = "") -> str:
    return "\t".join([
        "main", addr, "function", f"func_{addr}", ".text", f"func_{addr}", "4",
        "generated", "", "0", verify, gate, "generated", "rombytes",
    ])


class SchemaTests(unittest.TestCase):
    def test_gate_sits_next_to_verify(self):
        self.assertEqual(LEDGER_COLUMNS[LEDGER_COLUMNS.index("verify") + 1], "gate")

    def test_gate_default_is_empty(self):
        self.assertEqual(STATUS_DEFAULTS["gate"], "")
        self.assertIn("raw", GATE_VALUES)
        self.assertIn("reloc", GATE_VALUES)


class SetFieldsTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = Path(self._dir.name) / "ledger.tsv"
        self.path.write_text(HEADER + "\n" + row("60000000") + "\n"
                             + row("60000004", verify="match", gate="raw") + "\n")

    def tearDown(self):
        self._dir.cleanup()

    def test_writes_the_match_and_its_provenance_together(self):
        changed = set_fields(self.path, ("main", "60000000"),
                             {"verify": "match", "gate": "reloc"})
        self.assertEqual(sorted(changed), ["gate", "verify"])
        lines = self.path.read_text().splitlines()
        fields = lines[1].split("\t")
        self.assertEqual(fields[LEDGER_COLUMNS.index("verify")], "match")
        self.assertEqual(fields[LEDGER_COLUMNS.index("gate")], "reloc")

    def test_only_the_addressed_line_changes(self):
        before = self.path.read_text().splitlines()
        set_fields(self.path, ("main", "60000000"), {"verify": "match", "gate": "raw"})
        after = self.path.read_text().splitlines()
        self.assertEqual(before[0], after[0])
        self.assertEqual(before[2], after[2])

    def test_a_no_op_write_changes_nothing(self):
        before = self.path.read_text()
        changed = set_fields(self.path, ("main", "60000000"),
                             {"verify": "none", "gate": ""})
        self.assertEqual(changed, [])
        self.assertEqual(self.path.read_text(), before)

    def test_set_field_still_reports_a_boolean(self):
        self.assertTrue(set_field(self.path, ("main", "60000000"), "verify", "match"))
        self.assertFalse(set_field(self.path, ("main", "60000000"), "verify", "match"))

    def test_unknown_column_raises(self):
        with self.assertRaises(ValueError):
            set_fields(self.path, ("main", "60000000"), {"nope": "x"})

    def test_unknown_entry_raises(self):
        with self.assertRaises(KeyError):
            set_fields(self.path, ("main", "60000008"), {"verify": "match"})


if __name__ == "__main__":
    unittest.main()
