"""Regression tests for the ledger validator's robustness on malformed input.

The validator is the CI gate, so on a broken ledger it must *report* and return — never
crash. These pin the four former tracebacks (empty file, renamed/13-wide header, non-integer
``size``, non-hex ``addr``) plus the missing-``--blocks`` usage error and the happy path.

Pure functions + temp files — no clang, no Ghidra, no binary. Run with::

    python3 tests/ledger/test_validate.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

from ledgerlib import LEDGER_COLUMNS
from validate import main as validate_main
from validate import validate

HEADER = "\t".join(LEDGER_COLUMNS)


def row(**over) -> str:
    """One ledger row (correct column order) with ``over`` applied."""
    base = {
        "module": "main", "addr": "00000000", "kind": "function",
        "name": "func_00000000", "block": ".text", "group": "func_00000000",
        "size": "4", "name_class": "generated", "bind": "", "guess": "0",
        "verify": "none", "gate": "", "review": "generated", "enroll": "rombytes",
    }
    base.update(over)
    return "\t".join(base[c] for c in LEDGER_COLUMNS)


class ValidatorRobustnessTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def ledger(self, rows: list[str], header: str = HEADER) -> Path:
        p = self.tmp / "ledger.tsv"
        p.write_text(header + "\n" + "".join(r + "\n" for r in rows))
        return p

    # --- A4: an empty file ---------------------------------------------------------
    def test_empty_file_reports_instead_of_crashing(self):
        p = self.tmp / "empty.tsv"
        p.write_text("")
        self.assertEqual(validate(p, None), [f"{p}: empty ledger"])

    # --- A1: a wrong header that still has the right width -------------------------
    def test_renamed_header_column_reports_mismatch_without_crashing(self):
        bad = HEADER.replace("kind", "knd")
        errors = validate(self.ledger([row()], header=bad), None)
        self.assertTrue(any("header mismatch" in e for e in errors))

    # --- A2: a non-integer size ----------------------------------------------------
    def test_non_integer_size_is_reported_not_raised(self):
        p = self.ledger([row(size="XX"),
                         row(addr="00000004", name="func_00000004")])
        self.assertTrue(any("not an integer" in e for e in validate(p, None)))

    # --- A3: a non-hex address -----------------------------------------------------
    def test_non_hex_address_is_reported_not_raised(self):
        p = self.ledger([row(addr="ZZZZZZZZ", name="func_ZZZZZZZZ"),
                         row(addr="00000004", name="func_00000004")])
        self.assertTrue(any("not 8-hex" in e for e in validate(p, None)))

    # --- A5: a missing --blocks file -----------------------------------------------
    def test_missing_blocks_file_is_reported(self):
        p = self.ledger([row()])
        errors = validate(p, self.tmp / "nope.tsv")
        self.assertTrue(any("does not exist" in e for e in errors))

    # --- happy path ----------------------------------------------------------------
    def test_well_formed_ledger_has_no_errors(self):
        p = self.ledger([row(size="4"),
                         row(addr="00000004", name="func_00000004")])
        self.assertEqual(validate(p, None), [])

    def test_cli_on_a_renamed_header_returns_without_raising(self):
        # A1 also covers the summary path in main(), not just validate().
        bad = HEADER.replace("kind", "knd")
        p = self.ledger([row()], header=bad)
        self.assertEqual(validate_main(["--ledger", str(p)]), 1)


class GateProvenanceTests(unittest.TestCase):
    """``gate`` is evidence: it is set exactly when the entry has a match."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def ledger(self, rows: list[str]) -> Path:
        p = self.tmp / "ledger.tsv"
        p.write_text(HEADER + "\n" + "".join(r + "\n" for r in rows))
        return p

    def test_a_match_with_provenance_is_valid(self):
        p = self.ledger([row(verify="match", gate="reloc"),
                         row(addr="00000004", name="func_00000004")])
        self.assertEqual(validate(p, None), [])

    def test_a_match_without_provenance_is_reported(self):
        p = self.ledger([row(verify="match", gate=""),
                         row(addr="00000004", name="func_00000004")])
        self.assertTrue(any("no gate provenance" in e for e in validate(p, None)))

    def test_provenance_without_a_match_is_reported(self):
        p = self.ledger([row(verify="none", gate="raw"),
                         row(addr="00000004", name="func_00000004")])
        self.assertTrue(any("needs a match" in e for e in validate(p, None)))

    def test_an_unknown_gate_value_is_reported(self):
        p = self.ledger([row(verify="match", gate="guessed"),
                         row(addr="00000004", name="func_00000004")])
        self.assertTrue(any("bad gate" in e for e in validate(p, None)))

    def test_an_external_must_not_carry_provenance(self):
        ext = row(kind="external", addr="", name="_ZN2nn2fs4InitEv", block="",
                  group="", size="", name_class="discovered", bind="GLOBAL",
                  gate="raw", enroll="")
        p = self.ledger([row(), ext])
        self.assertTrue(any("external must have empty gate" in e for e in validate(p, None)))


if __name__ == "__main__":
    unittest.main()
