"""Tests for the repair loop (``tools/loop/repair.py``).

The loop's decisions are pure functions of the gate reports the caller supplies, so these
tests drive it with a scripted fake gate and a scripted fake model — no clang, no Ghidra, no
network. The property that matters is **monotonicity**: a reply is adopted only when it is
strictly closer, so a repair session can never end worse than the seed it started from.

Run with::

    python3 tests/loop/test_repair.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))

import repair
from repair import (
    MAX_DIFF_WORDS,
    RepairResult,
    UNREACHABLE,
    closeness,
    eligible,
    is_unreachable,
    repair as run_repair,
    strictly_closer,
)


def report(diff: int, cand: int = 60, ref: int = 60, ok: bool | None = None,
           status: str | None = None) -> dict:
    """A gate report with the fields the repair loop reads."""
    if status is None:
        status = "match" if (ok if ok is not None else diff == 0) else "mismatch"
    return {"ok": status == "match", "status": status,
            "cand_len": cand, "ref_len": ref, "diff_count": diff}


class FakeGate:
    """A gate driven by a source -> report map, remembering every source it judged."""

    def __init__(self, verdicts: dict[str, dict | None] | None = None,
                 default: dict | None = None):
        self.verdicts = verdicts or {}
        self.default = default
        self.seen: list[str] = []

    def __call__(self, source: str):
        self.seen.append(source)
        if source in self.verdicts:
            rep = self.verdicts[source]
        else:
            rep = self.default
        return rep, ("error: does not compile" if rep is None else "")


class FakeAsker:
    """Returns the scripted replies in order, remembering the prompts it was given."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.replies.pop(0) if self.replies else ""


def prompt_for(source, rep, out):  # pragma: no cover - exercised via the loop
    return f"prompt[{source}]"


class IsUnreachableTests(unittest.TestCase):
    def test_the_bare_sentinel(self):
        self.assertTrue(is_unreachable(UNREACHABLE))

    def test_leading_whitespace_and_case_insensitive(self):
        self.assertTrue(is_unreachable("  \n  unreachable — registers only"))
        self.assertTrue(is_unreachable("**UNREACHABLE**"))

    def test_real_code_is_not_the_sentinel(self):
        self.assertFalse(is_unreachable("int f(void) { return 0; }"))
        self.assertFalse(is_unreachable(""))

    def test_none_is_not_the_sentinel(self):
        self.assertFalse(is_unreachable(None))


class ClosenessTests(unittest.TestCase):
    def test_length_error_ranks_before_divergences(self):
        self.assertEqual(closeness(report(4, cand=56)), (4, 4))
        self.assertLess(closeness(report(1, cand=60)), closeness(report(0, cand=56)))

    def test_a_missing_report_is_infinitely_far(self):
        self.assertEqual(closeness(None)[0], 1 << 30)

    def test_strictly_closer_needs_an_improvement(self):
        self.assertTrue(strictly_closer(report(2), report(3)))
        self.assertFalse(strictly_closer(report(3), report(3)))
        self.assertFalse(strictly_closer(None, report(3)))


class EligibleTests(unittest.TestCase):
    def test_a_same_length_mismatch_is_repairable(self):
        ok, why = eligible(report(8))
        self.assertTrue(ok)
        self.assertIn("8 differing byte", why)

    def test_a_match_is_not_repairable(self):
        ok, why = eligible(report(0))
        self.assertFalse(ok)
        self.assertIn("already matches", why)

    def test_a_length_difference_is_not_repairable(self):
        ok, why = eligible(report(4, cand=56, status="body-length"))
        self.assertFalse(ok)
        self.assertIn("body-length", why)

    def test_too_far_is_not_repairable(self):
        ok, why = eligible(report(MAX_DIFF_WORDS * 4 + 1))
        self.assertFalse(ok)
        self.assertIn("exceeds", why)

    def test_exactly_at_the_budget_is_repairable(self):
        self.assertTrue(eligible(report(MAX_DIFF_WORDS * 4))[0])

    def test_no_report_is_not_repairable(self):
        ok, why = eligible(None)
        self.assertFalse(ok)
        self.assertIn("did not compile", why)

    def test_the_budget_is_configurable(self):
        self.assertFalse(eligible(report(12), max_diff_words=2)[0])
        self.assertTrue(eligible(report(12), max_diff_words=3)[0])


class RepairLoopTests(unittest.TestCase):
    SEED = "seed"

    def _run(self, verdicts, replies, rounds=4, default=None):
        gate = FakeGate(verdicts, default=default)
        ask = FakeAsker(replies)
        result = run_repair(self.SEED, gate=gate, ask=ask, prompt_for=prompt_for,
                            rounds=rounds)
        return result, gate, ask

    def test_a_seed_that_already_matches_is_accepted_without_asking(self):
        result, gate, ask = self._run({self.SEED: report(0)}, [])
        self.assertIsInstance(result, RepairResult)
        self.assertEqual(result.outcome, "match")
        self.assertFalse(result.improved)
        self.assertEqual(result.rounds_used, 0)
        self.assertEqual(ask.prompts, [])

    def test_a_matching_reply_becomes_the_source(self):
        result, gate, _ask = self._run(
            {self.SEED: report(8), "fix": report(0)}, ["fix"])
        self.assertEqual(result.outcome, "match")
        self.assertEqual(result.source, "fix")
        self.assertTrue(result.improved)
        self.assertEqual(result.rounds_used, 1)
        self.assertEqual(gate.seen, [self.SEED, "fix"])

    def test_a_closer_reply_is_kept_and_the_next_edit_builds_on_it(self):
        gate = FakeGate({self.SEED: report(12), "a": report(8), "b": report(0)})
        ask = FakeAsker(["a", "b"])
        prompts = []

        def pf(source, rep, out):
            prompts.append(source)
            return "p"

        result = run_repair(self.SEED, gate=gate, ask=ask, prompt_for=pf, rounds=4)
        self.assertEqual(result.outcome, "match")
        self.assertEqual(result.source, "b")
        self.assertEqual(prompts, [self.SEED, "a"])   # each round uses the best so far
        self.assertEqual(result.history, [(0, 12), (0, 8), (0, 0)])

    def test_a_worse_reply_is_discarded_and_the_best_survives(self):
        result, gate, _ask = self._run(
            {self.SEED: report(8), "closer": report(4), "worse": report(20)},
            ["closer", "worse"], rounds=2)
        self.assertEqual(result.outcome, "mismatch")
        self.assertEqual(result.source, "closer")
        self.assertEqual(repair_close(result.report), (0, 4))

    def test_the_round_budget_is_respected(self):
        result, gate, ask = self._run({self.SEED: report(8)}, ["x", "y", "z"], rounds=2,
                                      default=report(7))
        self.assertEqual(result.rounds_used, 2)
        self.assertEqual(len(gate.seen), 3)          # seed + two rounds
        self.assertEqual(len(ask.prompts), 2)

    def test_unreachable_stops_the_loop(self):
        result, gate, _ask = self._run({self.SEED: report(8)}, [UNREACHABLE, "never"],
                                       default=report(4))
        self.assertEqual(result.outcome, "mismatch")
        self.assertEqual(result.rounds_used, 1)
        self.assertEqual(len(gate.seen), 1)          # the sentinel is never gated
        self.assertEqual(result.source, self.SEED)

    def test_an_empty_reply_stops_the_loop(self):
        result, _gate, ask = self._run({self.SEED: report(8)}, ["   "])
        self.assertEqual(result.rounds_used, 1)
        self.assertEqual(len(ask.prompts), 1)

    def test_a_compile_failure_is_retried_and_never_adopted(self):
        result, gate, _ask = self._run(
            {self.SEED: report(8), "broken": None, "ok": report(4)},
            ["broken", "ok"], rounds=2)
        self.assertEqual(result.source, "ok")
        # history[0] is the seed; a compile failure ranks as infinitely far and is never kept.
        self.assertEqual(result.history, [(0, 8), (1 << 30, 1 << 30), (0, 4)])

    def test_an_ineligible_seed_asks_nothing(self):
        result, gate, ask = self._run({self.SEED: report(40)}, ["never"])
        self.assertEqual(ask.prompts, [])
        self.assertEqual(result.rounds_used, 0)
        self.assertEqual(result.outcome, "mismatch")

    def test_a_seed_that_does_not_compile_is_an_error(self):
        result, _gate, ask = self._run({self.SEED: None}, ["never"])
        self.assertEqual(result.outcome, "error")
        self.assertEqual(result.rounds_used, 0)
        self.assertEqual(ask.prompts, [])

    def test_an_empty_seed_is_an_error_without_gating(self):
        gate = FakeGate()
        result = run_repair("", gate=gate, ask=FakeAsker([]), prompt_for=prompt_for)
        self.assertEqual(result.outcome, "error")
        self.assertEqual(gate.seen, [])


def repair_close(rep):
    return closeness(rep)


if __name__ == "__main__":
    unittest.main()
