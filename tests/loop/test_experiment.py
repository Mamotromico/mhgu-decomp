"""Tests for the experiment report: benchmark-scoped aggregation (unique matches,
compile failures, near misses, tokens/cost), identity mixture warnings, and the
matched-set attribution of --compare. All synthetic. Run with::

    python3 tests/loop/test_report.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ledger"))

import attempts
import benchmark
import nearmiss
import experiment
from experiment import compare, filter_records, identity_of, main, summarize

REPO = Path(__file__).resolve().parents[2]
TOOLCHAIN = REPO / "config" / "toolchain.json"

LEDGER_COLUMNS = ("module\taddr\tkind\tname\tblock\tgroup\tsize\tname_class\tbind\tguess"
                  "\tverify\tgate\treview\tenroll\n")


def ledger_row(addr: str, verify: str = "none") -> str:
    return (f"main\t{addr}\tfunction\tfunc_{addr}\t.text\tfunc_{addr}\t64"
            f"\tgenerated\t\t0\t{verify}\t\tgenerated\trombytes\n")


def record(rid: int, addr: str, *, experiment: str | None = "control",
           outcome: str = "mismatch", source: str = "model", kind: str = "plain",
           gate_rc: int = 0, prompt: int | None = 100, completion: int | None = 40,
           reasoning: int | None = 0, latency: float = 1.0, cost: float | None = 0.002,
           provider: str = "p", model_name: str = "m", toolchain: str = "t") -> dict:
    r = {"id": rid, "module": "main", "addr": addr, "name": f"func_{addr}",
         "outcome": outcome, "source": source, "kind": kind, "gate_rc": gate_rc,
         "prompt_tokens": prompt, "completion_tokens": completion,
         "reasoning_tokens": reasoning, "latency_s": latency,
         "provider": provider, "requested_model": model_name,
         "toolchain_sha256": toolchain, "gate_version": "bytegate/v4",
         "decoding": {"temperature": 0.0}, "experiment": experiment}
    if cost is not None:
        r["cost_usd"] = cost
    return r


def bench_entries(addrs_splits: dict[str, str]) -> list[dict]:
    return [{"module": "main", "addr": a, "name": f"func_{a}", "size": 64, "body": 64,
             "cohorts": ["33-64B", "calls"], "split": s}
            for a, s in addrs_splits.items()]


class FilterAndIdentityTests(unittest.TestCase):
    def test_filter_scopes_to_keys_and_variant(self):
        records = [record(1, "60000000"), record(2, "60000000", experiment="other"),
                   record(3, "60000008"), record(4, "ffffff00")]
        scoped = filter_records(records, {("main", "60000000"), ("main", "60000008")},
                                "control")
        self.assertEqual([r["id"] for r in scoped], [1, 3])
        any_variant = filter_records(records, {("main", "60000000"), ("main", "60000008")},
                                     None)
        self.assertEqual([r["id"] for r in any_variant], [1, 2, 3])

    def test_identity_collects_and_flags_mixtures(self):
        one = identity_of([record(1, "60000000"), record(2, "60000000")])
        self.assertEqual(one["mixed"], [])
        two = identity_of([record(1, "60000000"), record(2, "60000000", toolchain="other")])
        self.assertEqual(two["mixed"], ["toolchain_sha256"])
        plain = identity_of([{"id": 1}])
        self.assertEqual(plain["values"]["provider"], [])


class SummarizeTests(unittest.TestCase):
    def setUp(self):
        self.entries = bench_entries({"60000000": "dev", "60000004": "holdout",
                                      "60000008": "dev"})
        self.keys = {("main", a) for a in ("60000000", "60000004", "60000008")}
        self.pin = nearmiss.eval_pin(TOOLCHAIN)
        bank = nearmiss.empty_bank()
        nearmiss.upsert(bank, "main", "60000004", [0, 3], self.pin, attempt_id=9)
        nearmiss.upsert(bank, "main", "60000008", [4, 1], self.pin, attempt_id=10)
        self.bank_close = {(r["module"], r["addr"]): list(r["closeness"])
                           for r in bank["records"].values()}

    def _summarize(self, records, ledger=None):
        ledger_verify = ledger or {k: "none" for k in self.keys}
        return summarize(records, self.entries, bank_close=self.bank_close,
                         ledger_verify=ledger_verify)

    def test_unique_matches_count_entries_not_attempts(self):
        records = [record(1, "60000000", outcome="match"),
                   record(2, "60000000", outcome="match", kind="retry"),
                   record(3, "60000004", outcome="mismatch")]
        s = self._summarize(records)
        self.assertEqual(s["unique_matches"], 1)
        self.assertEqual(s["match_first_source"], {"model": 1})
        self.assertEqual(s["attempts"], 3)

    def test_template_and_repair_match_sources_are_distinguished(self):
        records = [record(1, "60000000", outcome="match", source="template",
                          prompt=None, completion=None, cost=None),
                   record(2, "60000004", outcome="match", source="repair", kind="repair")]
        s = self._summarize(records)
        self.assertEqual(s["match_first_source"], {"template": 1, "repair": 1})
        self.assertEqual(s["matches_by_repair"], 1)

    def test_compile_failures_and_near_misses(self):
        records = [record(1, "60000000", outcome="error", gate_rc=3),
                   record(2, "60000000", outcome="error", gate_rc=3),
                   record(3, "60000004", outcome="mismatch"),
                   record(4, "60000008", outcome="mismatch")]
        s = self._summarize(records)
        self.assertEqual(s["compile_failure_attempts"], 2)
        self.assertEqual(s["compile_failure_entries"], 1)
        # 60000004 has bank closeness [0, 3] -> exact-length near miss; 60000008 is [4, 1].
        self.assertEqual(s["exact_length_near_misses"], 1)

    def test_usage_totals_and_cost_absence(self):
        s = self._summarize([record(1, "60000000"), record(2, "60000004", cost=None)])
        self.assertEqual(s["tokens"], {"prompt": 200, "completion": 80, "reasoning": 0})
        self.assertAlmostEqual(s["cost_usd"], 0.002)
        self.assertTrue(s["cost_recorded"])
        free = self._summarize([record(1, "60000000", cost=None)])
        self.assertFalse(free["cost_recorded"])

    def test_cohorts_splits_and_outside_matches(self):
        records = [record(1, "60000000", outcome="match"),
                   record(2, "60000004", outcome="match")]
        s = self._summarize(records, ledger={("main", "60000000"): "match",
                                             ("main", "60000004"): "match",
                                             ("main", "60000008"): "match"})
        # 60000008 matched in the ledger with no variant record -> outside the experiment.
        self.assertEqual(s["matched_outside_experiment"], ["main/60000008"])
        self.assertEqual(s["splits"]["dev"]["matched"], 1)
        self.assertEqual(s["splits"]["holdout"]["matched"], 1)
        self.assertEqual(s["cohorts"]["33-64B"]["matched"], 2)


class CompareTests(unittest.TestCase):
    def test_attribution_by_earliest_matching_id(self):
        entries = bench_entries({"60000000": "dev", "60000004": "dev"})
        keys = {("main", a) for a in ("60000000", "60000004")}
        a = summarize([record(1, "60000000", outcome="match")], entries,
                      bank_close={}, ledger_verify={k: "none" for k in keys})
        b = summarize([record(5, "60000000", outcome="match"),
                       record(6, "60000004", outcome="match")], entries,
                      bank_close={}, ledger_verify={k: "none" for k in keys})
        cmp = compare({"control": a, "v2": b})
        self.assertEqual(cmp["only_control"], [])
        self.assertEqual(cmp["only_v2"], ["main/60000004"])
        self.assertEqual(cmp["attributed"], {"control": 1, "v2": 1})


class MainTests(unittest.TestCase):
    def test_end_to_end_with_compare(self):
        entries = bench_entries({"60000000": "dev", "60000004": "dev"})
        doc = {"format": 1, "name": "t", "created": "now", "inputs": {},
               "params": {"total": 2, "holdout_fraction": 0.5, "salt": "t"},
               "counts": {}, "entries": entries}
        doc["digest"] = benchmark.document_digest(doc)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "t.json").write_text(json.dumps(doc))
            store = td / "attempts"
            store.mkdir()
            log = [record(1, "60000000", experiment="control", outcome="match"),
                   record(2, "60000004", experiment="control"),
                   record(3, "60000000", experiment="v2", outcome="match"),
                   record(4, "60000004", experiment="v2", outcome="match")]
            with (store / "log.jsonl").open("w") as fh:
                for r in log:
                    fh.write(json.dumps(r) + "\n")
            (td / "ledger.tsv").write_text(LEDGER_COLUMNS + ledger_row("60000000")
                                           + ledger_row("60000004"))
            out = td / "report.json"
            rc = main(["--name", "t", "--dir", str(td), "--store", str(store),
                       "--ledger", str(td / "ledger.tsv"), "--toolchain", str(TOOLCHAIN),
                       "--bank", str(td / "no-such-bank.json"),
                       "--compare", "control,v2", "--json", str(out)])
            self.assertEqual(rc, 0)
            payload = json.loads(out.read_text())
            self.assertEqual(payload["variants"]["control"]["unique_matches"], 1)
            self.assertEqual(payload["variants"]["v2"]["unique_matches"], 2)
            self.assertEqual(payload["compare"]["only_v2"], ["main/60000004"])
            self.assertEqual(payload["compare"]["attributed"], {"control": 1, "v2": 1})

    def test_a_tampered_benchmark_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "t.json").write_text(json.dumps({"name": "t", "digest": "bogus"}))
            rc = main(["--name", "t", "--dir", str(td), "--variant", "x"])
            self.assertEqual(rc, 2)

    def test_compare_requires_exactly_two_names(self):
        rc = main(["--name", "t", "--dir", "/nonexistent", "--compare", "a,b,c"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
