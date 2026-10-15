"""Tests for the reconstruction driver's pure helpers and one stubbed iteration.

The impure steps are stubbed: ``run_subprocess`` is replaced with a fake gate that writes a
``--report`` file, and the model is a stub. That exercises the whole ``process()`` path —
write, gate, log, bank, move — without clang, Ghidra, or a model. Run with::

    python3 tests/loop/test_run.py
"""

from __future__ import annotations

import contextlib
import io
import json
import struct
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))

import attempts
import bundle
import model
import nearmiss
from run import (
    Feedback,
    Layout,
    attempt_entry,
    attempt_store,
    bank_path,
    build_prompt,
    bundle_argv,
    context_path,
    ensure_under,
    feedback_from_record,
    feedback_section,
    gate_argv,
    group_is_single,
    has_nonstack_block_move,
    parse_reference_instructions,
    process,
    prompt_fingerprint,
    resolve_entry,
    safe_draft_path,
    select_next,
)


def entry(addr="601a72e4", name=None, module="main", group=None,
          kind="function", verify="none") -> dict:
    name = name or f"func_{addr}"
    return {"module": module, "addr": addr, "name": name, "group": group or name,
            "kind": kind, "verify": verify}


def layout(root: Path) -> Layout:
    return Layout(ledger=Path("/ledger"), inventory=Path("/inv"), nso=Path("/nso"),
                  context=Path("/ctx"), src_root=root, build_config=Path("/bc"),
                  toolchain=Path("/tc"), work=Path("/work"))


class SafeDraftPathTests(unittest.TestCase):
    def test_ledger_derived_path(self):
        self.assertEqual(safe_draft_path(entry(), Path("/r/src")),
                         Path("/r/src/main/func_601a72e4.cpp"))

    def test_rejects_separator_in_group(self):
        with self.assertRaises(ValueError):
            safe_draft_path(entry(group="../evil"), Path("/r/src"))

    def test_rejects_backslash_and_dotdot(self):
        for bad in ("a/b", "a\\b", "..", "."):
            with self.assertRaises(ValueError):
                safe_draft_path(entry(group=bad), Path("/r/src"))


class EnsureUnderTests(unittest.TestCase):
    def test_accepts_under_root(self):
        self.assertTrue(ensure_under(Path("/r/src/main/x.cpp"), Path("/r/src")))

    def test_rejects_outside_root(self):
        with self.assertRaises(ValueError):
            ensure_under(Path("/r/src/../etc/passwd"), Path("/r/src"))


class PathHelperTests(unittest.TestCase):
    def test_context_and_store_paths(self):
        lay = layout(Path("/r/src"))
        self.assertEqual(context_path(lay, entry()), Path("/ctx/main/601a72e4.md"))
        self.assertEqual(attempt_store(lay), Path("/work/attempts"))
        self.assertEqual(bank_path(lay), Path("/work/nearmiss/bank.json"))


class GroupIsSingleTests(unittest.TestCase):
    def test_single_function_group(self):
        self.assertTrue(group_is_single([entry()], "main", "func_601a72e4"))

    def test_merged_group_is_not_single(self):
        entries = [entry(), entry(addr="601a72e8", group="func_601a72e4")]
        self.assertFalse(group_is_single(entries, "main", "func_601a72e4"))

    def test_data_entries_do_not_count(self):
        entries = [entry(), entry(kind="data", group="func_601a72e4")]
        self.assertTrue(group_is_single(entries, "main", "func_601a72e4"))


class BuildPromptTests(unittest.TestCase):
    def test_valid_identifier_needs_no_asm_label(self):
        prompt = build_prompt(entry(), "BUNDLE-TEXT")
        self.assertIn("`func_601a72e4`", prompt)
        self.assertNotIn('asm("func_601a72e4")', prompt)
        self.assertIn("inline assembly", prompt)
        self.assertIn("BUNDLE-TEXT", prompt)

    def test_non_identifier_name_uses_an_asm_label(self):
        prompt = build_prompt(entry(name="weird.name"), "B")
        self.assertIn('asm("weird.name")', prompt)

    def test_struct_copy_section_is_omitted_without_a_block_move(self):
        # Most functions have only a push/pop save; the copy guidance must not appear.
        bundle = "## disassembly\n\n    60035efc  e1a02000  mov     r2, r0\n"
        prompt = build_prompt(entry(), bundle)
        self.assertNotIn("by-value struct copy", prompt)
        self.assertNotIn("Worked example", prompt)
        self.assertIn("field's offset", prompt)   # the general layout guidance stays

    def test_struct_copy_section_is_included_with_a_nonstack_block_move(self):
        bundle = ("## disassembly\n\n"
                  "    60010000  e8910003  ldmia   r1, {r0,r1}\n")
        prompt = build_prompt(entry(), bundle)
        self.assertIn("by-value struct copy", prompt)
        self.assertIn("Worked example", prompt)

    def test_a_push_is_not_a_nonstack_block_move(self):
        bundle = ("## disassembly\n\n"
                  "    60010000  e92d4830  stmdb   sp!, {r4,r5,r11,lr}\n"
                  "    60010004  e8bd8830  ldmia   sp!, {r4,r5,pc}\n")
        self.assertFalse(has_nonstack_block_move(bundle))

    def test_nonstack_block_move_detected(self):
        bundle = "    60010000  e8910003  ldmia   r1, {r0,r1}\n"
        self.assertTrue(has_nonstack_block_move(bundle))

    def test_empty_bundle_has_no_block_move(self):
        self.assertFalse(has_nonstack_block_move(""))


class ArgvTests(unittest.TestCase):
    def test_gate_argv_is_fixed_and_updates(self):
        argv = gate_argv(layout(Path("/r/src")), entry(), 60)
        self.assertIn("--update", argv)
        self.assertEqual(argv[argv.index("--body") + 1], "60")
        self.assertEqual(argv[argv.index("--src-root") + 1], "/r/src")
        self.assertTrue(all(isinstance(a, str) for a in argv))

    def test_gate_argv_adds_a_report_path(self):
        argv = gate_argv(layout(Path("/r/src")), entry(), 60, Path("/tmp/r.json"))
        self.assertEqual(argv[argv.index("--report") + 1], "/tmp/r.json")

    def test_bundle_argv_targets_the_entry_and_body(self):
        argv = bundle_argv(layout(Path("/r/src")), entry(), 60)
        self.assertEqual(argv[-4:], ["--out", "/ctx", "--body", "60"])
        self.assertIn("601a72e4", argv)


class ResolveEntryTests(unittest.TestCase):
    def test_uses_the_given_module(self):
        entries = [entry(module="other")]
        self.assertEqual(resolve_entry(entries, "other", "601a72e4")["module"], "other")

    def test_normalizes_the_address(self):
        self.assertEqual(resolve_entry([entry()], "main", "0x601A72E4")["addr"], "601a72e4")

    def test_wrong_module_raises(self):
        with self.assertRaises(bundle.BundleError):
            resolve_entry([entry()], "other", "601a72e4")


class SelectNextTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        (self.tmp / "src" / "main").mkdir(parents=True)
        self.lay = layout(self.tmp / "src")

    def tearDown(self):
        self._dir.cleanup()

    def test_picks_first_by_order(self):
        entries = [entry(addr="601a72e4"), entry(addr="60000024")]
        nxt = select_next(entries, self.lay, skip_existing=True, done=set())
        assert nxt is not None
        self.assertEqual(nxt["addr"], "60000024")

    def test_done_entries_are_skipped(self):
        entries = [entry(addr="60000024"), entry(addr="60000f8c")]
        done = {("main", "60000024")}
        nxt = select_next(entries, self.lay, skip_existing=True, done=done)
        assert nxt is not None
        self.assertEqual(nxt["addr"], "60000f8c")

    def test_skip_existing_drops_entries_with_a_source(self):
        (self.tmp / "src" / "main" / "func_60000024.cpp").write_text("x")
        entries = [entry(addr="60000024"), entry(addr="60000f8c")]
        nxt = select_next(entries, self.lay, skip_existing=True, done=set())
        assert nxt is not None
        self.assertEqual(nxt["addr"], "60000f8c")

    def test_exhausted_returns_none(self):
        self.assertIsNone(select_next([], self.lay, skip_existing=True, done=set()))


class PromptFingerprintTests(unittest.TestCase):
    def test_deterministic_and_short(self):
        self.assertEqual(prompt_fingerprint("abc"), prompt_fingerprint("abc"))
        self.assertEqual(len(prompt_fingerprint("abc")), 16)

    def test_changes_with_input(self):
        self.assertNotEqual(prompt_fingerprint("a"), prompt_fingerprint("b"))


class _FakeModel:
    """Stands in for the HTTP client: returns a fixed candidate."""

    def __init__(self, text='extern "C" int func_601a72e4() { return 0; }'):
        self.text = text

    def complete(self, prompt, *, system=None):
        return Namespace(text=self.text, model="fake", prompt_tokens=1,
                         completion_tokens=2, latency_s=0.0)


def fake_gate(rc: int, status: str, diff_count: int, cand_len: int, diff_words=None):
    """A ``run_subprocess`` stand-in that writes the gate's ``--report`` file."""
    def _run(argv):
        report = None
        if "--report" in argv:
            report = Path(argv[argv.index("--report") + 1])
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps({
                "module": "main", "addr": "601a72e4", "name": "func_601a72e4",
                "ok": rc == 0, "status": status, "body": 60, "partition": 1368,
                "cand_len": cand_len, "ref_len": 60, "diff_count": diff_count,
                "first_diff": 0 if diff_count else None, "diff_words": diff_words or [],
                "has_reloc": False}))
        return rc, f">>> {status.upper()}"
    return _run


class ProcessTests(unittest.TestCase):
    """End-to-end of one iteration, with the gate and model stubbed out."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        root = Path(self._dir.name)
        self.md = root / "ctx" / "main" / "601a72e4.md"
        self.md.parent.mkdir(parents=True)
        self.md.write_text("# bundle: func_601a72e4\n")
        inv = root / "inventory.tsv"
        inv.write_text("601a72e4\tfunction\t60\tFUN\n")
        toolchain = root / "toolchain.json"
        toolchain.write_text('{"clang": "clang"}')
        self.lay = Layout(ledger=Path("/ledger"), inventory=inv, nso=Path("/nso"),
                          context=root / "ctx", src_root=root / "src",
                          build_config=Path("/bc"), toolchain=toolchain, work=root / "work")
        self.args = Namespace(body=None, rebuild=False, dry_run=False, force=False)
        self.draft = self.lay.src_root / "main" / "func_601a72e4.cpp"

    def tearDown(self):
        self._dir.cleanup()

    def log(self) -> list[dict]:
        return attempts.read_attempts(attempt_store(self.lay) / "log.jsonl")

    def bank_best(self) -> dict | None:
        bank = nearmiss.load_bank(bank_path(self.lay))
        return bank["records"].get("main:601a72e4")

    def _template_text(self, addr: str = "601a72e4") -> bytes:
        """A reference `.text` whose body at ``addr`` is `bx lr` (template rule #1)."""
        off = int(addr, 16) - 0x60000000
        raw = bytearray(off + 4)
        raw[off:off + 4] = struct.pack("<I", 0xE12FFF1E)
        return bytes(raw)

    def test_template_match_reports_the_rule(self):
        self.args.body = 4
        with (mock.patch("run.run_subprocess", new=fake_gate(0, "match", 0, 4)),
              contextlib.redirect_stdout(io.StringIO()) as out):
            outcome = process(entry(), [entry()], self.lay, self.args, None,
                              raw_text=self._template_text())
        self.assertEqual(outcome, "match")
        self.assertIn("template rule #1: void-return", out.getvalue())
        self.assertEqual(self.log()[0]["template_rule"], {"n": 1, "name": "void-return"})

    def test_match_keeps_src_records_attempt_and_does_not_bank(self):
        with mock.patch("run.run_subprocess", new=fake_gate(0, "match", 0, 60)):
            outcome = process(entry(), [entry()], self.lay, self.args, _FakeModel())
        self.assertEqual(outcome, "match")
        self.assertTrue(self.draft.exists())
        self.assertEqual(self.log()[0]["outcome"], "match")
        self.assertIsNone(self.bank_best())

    def test_mismatch_removes_draft_logs_and_banks_closeness(self):
        with mock.patch("run.run_subprocess", new=fake_gate(1, "mismatch", 3, 58)):
            outcome = process(entry(), [entry()], self.lay, self.args, _FakeModel())
        self.assertEqual(outcome, "mismatch")
        self.assertFalse(self.draft.exists())
        self.assertEqual(self.log()[0]["outcome"], "mismatch")
        self.assertNotIn("template_rule", self.log()[0])   # a model attempt, no rule
        banked = self.bank_best()
        assert banked is not None
        self.assertEqual(banked["closeness"], [2, 3])  # (len delta, divergences)

    def test_bank_keeps_the_closest_attempt(self):
        with mock.patch("run.run_subprocess", new=fake_gate(1, "mismatch", 2, 55)):
            process(entry(), [entry()], self.lay, self.args, _FakeModel())
        with mock.patch("run.run_subprocess", new=fake_gate(1, "mismatch", 7, 59)):
            process(entry(), [entry()], self.lay, self.args, _FakeModel())
        banked = self.bank_best()
        assert banked is not None
        self.assertEqual(banked["closeness"], [1, 7])  # len delta 1 beats 5
        self.assertEqual([r["parent"] for r in self.log()], [None, 1])

    def test_merged_tu_keeps_draft_on_mismatch(self):
        entries = [entry(), entry(addr="601a72e8", group="func_601a72e4")]
        with mock.patch("run.run_subprocess", new=fake_gate(1, "mismatch", 3, 58)):
            process(entry(), entries, self.lay, self.args, _FakeModel())
        self.assertTrue(self.draft.exists())

    def test_empty_candidate_makes_no_attempt(self):
        with mock.patch("run.run_subprocess", new=fake_gate(0, "match", 0, 60)):
            outcome = process(entry(), [entry()], self.lay, self.args, _FakeModel("   "))
        self.assertEqual(outcome, "error")
        self.assertFalse(self.draft.exists())
        self.assertEqual(self.log(), [])
        self.assertIsNone(self.bank_best())

    def test_compile_error_is_error_not_match_and_not_banked(self):
        # rc 3 (compilation failed) writes no report; the outcome must not read "mismatch".
        with mock.patch("run.run_subprocess", return_value=(3, "error: compilation failed")):
            outcome = process(entry(), [entry()], self.lay, self.args, _FakeModel())
        self.assertEqual(outcome, "error")
        self.assertFalse(self.draft.exists())
        self.assertEqual(self.log()[0]["outcome"], "error")
        self.assertIsNone(self.bank_best())

    def test_diff_words_are_recorded_and_feedback_is_flagged(self):
        words = [{"offset": 0, "got": "5c1080e5", "want": "170a80ed"}]
        fb = Feedback("mismatch", status="mismatch", diff_count=3, diff_words=words)
        with mock.patch("run.run_subprocess", new=fake_gate(1, "mismatch", 3, 58,
                                                            diff_words=words)):
            process(entry(), [entry()], self.lay, self.args, _FakeModel(), feedback=fb)
        record = self.log()[0]
        self.assertEqual(record["diff_words"], words)
        self.assertTrue(record["feedback_used"])

    def test_first_attempt_records_no_feedback_flag(self):
        with mock.patch("run.run_subprocess", new=fake_gate(1, "mismatch", 3, 58)):
            process(entry(), [entry()], self.lay, self.args, _FakeModel())
        self.assertNotIn("feedback_used", self.log()[0])


class AttemptEntryTests(unittest.TestCase):
    """The per-entry retry loop, with the single-attempt step stubbed."""

    def setUp(self):
        self.args = Namespace(attempts=3)
        self.entry = entry()

    def _run(self, one):
        return attempt_entry(self.entry, [], layout(Path("/r/src")), self.args, None, one=one)

    def test_stops_on_first_match(self):
        calls = []

        def one(*_):
            calls.append(1)
            return "match"

        self.assertEqual(self._run(one), ("match", 1))
        self.assertEqual(len(calls), 1)

    def test_retries_mismatch_up_to_the_limit(self):
        calls = []

        def one(*_):
            calls.append(1)
            return "mismatch"

        self.assertEqual(self._run(one), ("mismatch", 3))
        self.assertEqual(len(calls), 3)

    def test_matches_on_a_later_attempt(self):
        outcomes = iter(["mismatch", "mismatch", "match"])

        def one(*_):
            return next(outcomes)

        self.assertEqual(self._run(one), ("match", 3))

    def test_transport_error_is_retried(self):
        calls = []

        def one(*_):
            calls.append(1)
            raise model.ModelError("boom")

        self.assertEqual(self._run(one), ("error", 3))
        self.assertEqual(len(calls), 3)

    def test_attempt_error_is_retried(self):
        calls = []

        def one(*_):
            calls.append(1)
            raise attempts.AttemptError("corrupt log")

        self.assertEqual(self._run(one), ("error", 3))
        self.assertEqual(len(calls), 3)

    def test_dry_run_previews_once(self):
        calls = []

        def one(*_):
            calls.append(1)
            return "dry-run"

        self.assertEqual(self._run(one), ("dry-run", 1))
        self.assertEqual(len(calls), 1)

    def test_keyboard_interrupt_is_not_swallowed(self):
        def one(*_):
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            self._run(one)


class ReferenceInstructionsTests(unittest.TestCase):
    BUNDLE = ("## disassembly\n\n"
              "    601a72e4  5c1080e5  str r1, [r0, #92]\n"
              "    601a72e8  1eff2fe1  bx lr\n"
              "## calls\n\n    (none)\n")

    def test_offsets_are_body_relative(self):
        ref = parse_reference_instructions(self.BUNDLE, "601a72e4")
        self.assertEqual(ref[0], "str r1, [r0, #92]")
        self.assertEqual(ref[4], "bx lr")

    def test_only_the_disassembly_section_is_read(self):
        ref = parse_reference_instructions(self.BUNDLE, "601a72e4")
        self.assertNotIn(8, ref)


class FeedbackSectionTests(unittest.TestCase):
    BUNDLE = ("## disassembly\n\n"
              "    601a72e4  5c1080e5  str r1, [r0, #92]\n"
              "    601a72e8  1eff2fe1  bx lr\n")

    def test_no_feedback_is_empty(self):
        self.assertEqual(feedback_section(entry(), self.BUNDLE, None), "")

    def test_mismatch_names_the_instruction_and_quotes_the_candidate(self):
        fb = Feedback("mismatch", status="mismatch", diff_count=3,
                      diff_words=[{"offset": 0, "got": "5c1080e5", "want": "170a80ed"}],
                      candidate='extern "C" void f(void *p) { *(int *)p = 0; }')
        out = feedback_section(entry(), self.BUNDLE, fb)
        self.assertIn("Previous attempt did not match", out)
        self.assertIn("got 5c1080e5", out)
        self.assertIn("want 170a80ed", out)
        self.assertIn("original: str r1, [r0, #92]", out)   # the reference mnemonic
        self.assertIn("your previous translation unit", out)

    def test_compile_error_is_quoted(self):
        fb = Feedback("error", compile_error="x.cpp:1:1: error: expected ';'")
        out = feedback_section(entry(), self.BUNDLE, fb)
        self.assertIn("did not compile", out)
        self.assertIn("expected ';'", out)


class FeedbackFromRecordTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def test_none_without_an_actionable_outcome(self):
        self.assertIsNone(feedback_from_record(None, self.root))
        self.assertIsNone(feedback_from_record({"outcome": "match"}, self.root))

    def test_mismatch_reads_the_previous_candidate(self):
        blob = self.root / "main" / "601a72e4" / "001.cpp"
        blob.parent.mkdir(parents=True)
        blob.write_text("int f(void){return 0;}")
        rec = {"outcome": "mismatch", "gate_status": "mismatch", "diff_count": 3,
               "diff_words": [{"offset": 0, "got": "aa", "want": "bb"}],
               "candidate": "main/601a72e4/001.cpp"}
        fb = feedback_from_record(rec, self.root)
        self.assertEqual(fb.outcome, "mismatch")
        self.assertEqual(fb.diff_count, 3)
        self.assertEqual(fb.diff_words, [{"offset": 0, "got": "aa", "want": "bb"}])
        self.assertEqual(fb.candidate, "int f(void){return 0;}")

    def test_error_carries_the_compiler_output(self):
        rec = {"outcome": "error", "gate_output": "error: boom"}
        fb = feedback_from_record(rec, self.root)
        self.assertEqual(fb.outcome, "error")
        self.assertEqual(fb.compile_error, "error: boom")
        self.assertIsNone(fb.candidate)


class BuildPromptFeedbackTests(unittest.TestCase):
    def test_no_feedback_leaves_the_prompt_unchanged(self):
        self.assertNotIn("Previous attempt", build_prompt(entry(), "BUNDLE"))

    def test_feedback_is_appended(self):
        fb = Feedback("mismatch", status="mismatch", diff_count=1,
                      diff_words=[{"offset": 0, "got": "aabbccdd", "want": "11223344"}])
        out = build_prompt(entry(), "## disassembly\n\n    601a72e4  aabbccdd  mov r0, r0\n", fb)
        self.assertIn("Previous attempt did not match", out)
        self.assertIn("want 11223344", out)


class AttemptEntryFeedbackTests(unittest.TestCase):
    """Feedback threads between attempts; a repeated divergence stops the retry early."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)
        self.lay = Layout(ledger=Path("/ledger"), inventory=Path("/inv"), nso=Path("/nso"),
                          context=self.root / "ctx", src_root=self.root / "src",
                          build_config=Path("/bc"), toolchain=Path("/tc"),
                          work=self.root / "work")
        self.store = self.root / "work" / "attempts"

    def tearDown(self):
        self._dir.cleanup()

    def _attempt(self, one, attempts):
        self.args = Namespace(attempts=attempts)
        return attempt_entry(entry(), [], self.lay, self.args, None, one=one)

    def test_feedback_is_threaded_between_attempts(self):
        seen = []
        words = [{"offset": 0, "got": "aa", "want": "bb"}]

        def one(e, entries, lay, args, model, raw_text, feedback=None):
            seen.append(feedback)
            attempts.append(self.store, {
                "module": "main", "addr": "601a72e4", "name": "func_601a72e4",
                "outcome": "mismatch", "gate_status": "mismatch", "diff_count": 3,
                "diff_words": words}, candidate_text="int f(void){return 0;}")
            return "mismatch"

        outcome, used = self._attempt(one, 3)
        self.assertEqual(outcome, "mismatch")
        self.assertIsNone(seen[0])                       # the first attempt is the base prompt
        self.assertIsNotNone(seen[1])                    # the retry carries feedback
        self.assertEqual(seen[1].diff_words, words)
        self.assertEqual(seen[1].candidate, "int f(void){return 0;}")

    def test_a_repeated_divergence_stops_the_retry(self):
        words = [{"offset": 0, "got": "aa", "want": "bb"}]
        calls = []

        def one(e, entries, lay, args, model, raw_text, feedback=None):
            calls.append(feedback)
            attempts.append(self.store, {
                "module": "main", "addr": "601a72e4", "name": "func_601a72e4",
                "outcome": "mismatch", "gate_status": "mismatch", "diff_count": 3,
                "diff_words": words}, candidate_text="int f(void){return 0;}")
            return "mismatch"

        outcome, used = self._attempt(one, 5)
        self.assertEqual((outcome, used), ("mismatch", 2))   # stopped after the repeat, not 5
        self.assertEqual(len(calls), 2)

    def test_no_feedback_disables_both_feedback_and_the_stall_stop(self):
        words = [{"offset": 0, "got": "aa", "want": "bb"}]
        seen = []

        def one(e, entries, lay, args, model, raw_text, feedback=None):
            seen.append(feedback)
            attempts.append(self.store, {
                "module": "main", "addr": "601a72e4", "name": "func_601a72e4",
                "outcome": "mismatch", "gate_status": "mismatch", "diff_count": 3,
                "diff_words": words}, candidate_text="int f(void){return 0;}")
            return "mismatch"

        self.args = Namespace(attempts=3, feedback=False)
        outcome, used = attempt_entry(entry(), [], self.lay, self.args, None, one=one)
        self.assertEqual(used, 3)
        self.assertTrue(all(f is None for f in seen))


class AttemptEntryCompileBudgetTests(unittest.TestCase):
    """Non-compiling candidates draw on their own budget, not the match attempts."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)
        self.lay = Layout(ledger=Path("/ledger"), inventory=Path("/inv"), nso=Path("/nso"),
                          context=self.root / "ctx", src_root=self.root / "src",
                          build_config=Path("/bc"), toolchain=Path("/tc"),
                          work=self.root / "work")
        self.store = self.root / "work" / "attempts"

    def tearDown(self):
        self._dir.cleanup()

    def _compile_failing(self, calls):
        def one(e, entries, lay, args, model, raw_text, feedback=None):
            calls.append(feedback)
            attempts.append(self.store, {
                "module": "main", "addr": "601a72e4", "name": "func_601a72e4",
                "outcome": "error", "gate_rc": 3,
                "gate_output": "error: compilation failed (clang exit 1)"},
                candidate_text="int f(void){ return nope; }")
            return "error"
        return one

    def test_stops_at_the_compile_failure_budget(self):
        calls = []
        args = Namespace(attempts=5, compile_attempts=2)
        outcome, used = attempt_entry(entry(), [], self.lay, args, None,
                                      one=self._compile_failing(calls))
        self.assertEqual((outcome, used), ("error", 2))
        self.assertEqual(len(calls), 2)

    def test_budget_is_independent_of_the_match_attempts(self):
        calls = []
        args = Namespace(attempts=6, compile_attempts=3)
        outcome, used = attempt_entry(entry(), [], self.lay, args, None,
                                      one=self._compile_failing(calls))
        self.assertEqual(used, 3)                       # the compile budget, not the 6 attempts

    def test_a_mismatch_does_not_consume_the_compile_budget(self):
        calls = []

        def one(e, entries, lay, args, model, raw_text, feedback=None):
            calls.append(1)
            attempts.append(self.store, {
                "module": "main", "addr": "601a72e4", "name": "func_601a72e4",
                "outcome": "mismatch", "gate_status": "mismatch", "diff_count": 3,
                "diff_words": []}, candidate_text="int f(void){return 0;}")
            return "mismatch"

        args = Namespace(attempts=4, compile_attempts=2, feedback=False)
        outcome, used = attempt_entry(entry(), [], self.lay, args, None, one=one)
        self.assertEqual((outcome, used), ("mismatch", 4))
        self.assertEqual(len(calls), 4)

    def test_transport_errors_do_not_consume_the_compile_budget(self):
        calls = []

        def one(*_):
            calls.append(1)
            raise model.ModelError("boom")             # appends no record

        args = Namespace(attempts=4, compile_attempts=2)
        outcome, used = attempt_entry(entry(), [], self.lay, args, None, one=one)
        self.assertEqual((outcome, used), ("error", 4))
        self.assertEqual(len(calls), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
