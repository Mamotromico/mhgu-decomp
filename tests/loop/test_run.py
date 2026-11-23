"""Tests for the reconstruction driver's pure helpers and one stubbed iteration.

The impure steps are stubbed: ``run_subprocess`` is replaced with a fake gate that writes a
``--report`` file, and the model is a stub. That exercises the whole ``process()`` path —
write, gate, log, bank, move — without clang, Ghidra, or a model. Run with::

    python3 tests/loop/test_run.py
"""

from __future__ import annotations

import contextlib
import hashlib
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
    SYSTEM,
    Feedback,
    Layout,
    asm_violation,
    attempt_entry,
    attempt_store,
    attempted_counts,
    bank_path,
    bank_priorities,
    build_prompt,
    bundle_argv,
    context_path,
    describe_word_diff,
    ensure_under,
    feedback_from_record,
    feedback_section,
    gate_argv,
    gate_body,
    group_is_single,
    has_bit_op,
    has_guarded_return,
    has_mask_for_address,
    has_nonstack_block_move,
    parse_reference_instructions,
    process,
    bank_seeds,
    process_repair,
    prompt_fingerprint,
    repair_prompt,
    resolve_entry,
    safe_draft_path,
    select_next,
    truncated,
)


def entry(addr="601a72e4", name=None, module="main", group=None,
          kind="function", verify="none") -> dict:
    name = name or f"func_{addr}"
    return {"module": module, "addr": addr, "name": name, "group": group or name,
            "kind": kind, "verify": verify, "size": "1368"}


def layout(root: Path, work: Path | None = None) -> Layout:
    return Layout(ledger=Path("/ledger"), inventory=Path("/inv"), nso=Path("/nso"),
                  context=Path("/ctx"), src_root=root, build_config=Path("/bc"),
                  toolchain=Path("/tc"), work=work or Path("/work"))


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


class GateBodyTests(unittest.TestCase):
    """The gate extent includes reference pool words and never falls back to a prefix."""

    def test_a_leaf_keeps_the_inventory_extent(self):
        self.assertEqual(gate_body(b"\x1e\xff\x2f\xe1", 4, 1368), 4)

    def test_a_pool_reader_includes_padding_and_its_pool_word(self):
        # `ldr r0, [pc, #4]` targets offset 12: four padding bytes, then one pool word.
        body = b"\x04\x00\x9f\xe5\x1e\xff\x2f\xe1"
        self.assertEqual(gate_body(body, 8, 16), 16)

    def test_no_reference_bytes_fails_closed(self):
        with self.assertRaises(ValueError):
            gate_body(None, 8, 16)

    def test_invalid_pool_target_fails_closed(self):
        body = b"\x10\x00\x9f\xe5"
        with self.assertRaises(ValueError):
            gate_body(body, 4, 24)


class GotReferencePromptTests(unittest.TestCase):
    """A named pool target switches on the data-reference guidance."""

    def test_a_named_pool_target_includes_the_section(self):
        bundle = ("    6002b8f0  e59f100c  ldr  r1, [0x6002b904]  "
                  "; = 0x0180da60 -> D_61730ebc\n")
        prompt = build_prompt(entry(), bundle)
        self.assertIn("-> D_61730ebc", prompt)
        self.assertIn("NOT a constant", prompt)

    def test_a_plain_bundle_omits_it(self):
        self.assertNotIn("NOT a constant", build_prompt(entry(), "BUNDLE-TEXT"))


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

    def test_bit_op_detected_from_the_mnemonic(self):
        for insn in ("rbit    r0, r0", "ubfx    r0, r1, #4, #8", "bfc     r1, #6, #20",
                     "bfi     r2, r1, #0, #4", "revsh   r0, r0", "clz     r0, r0"):
            self.assertTrue(has_bit_op(f"    60010000  e7e00000  {insn}\n"), insn)

    def test_a_plain_function_has_no_bit_op(self):
        self.assertFalse(has_bit_op("    60035efc  e1a02000  mov     r2, r0\n"))
        self.assertFalse(has_bit_op(""))

    def test_bit_op_section_is_included_only_when_needed(self):
        plain = "    60035efc  e1a02000  mov     r2, r0\n"
        self.assertNotIn("__builtin_arm_rbit", build_prompt(entry(), plain))
        with_bit = build_prompt(entry(), "    60035efc  e7e00000  rbit    r0, r0\n")
        self.assertIn("__builtin_arm_rbit", with_bit)
        self.assertIn("__builtin_arm_bfc", with_bit)   # named as NOT existing

    def test_negative_padding_warning_is_always_present(self):
        self.assertIn("subtracted the wrong way round", build_prompt(entry(), ""))

    def test_empty_bundle_has_no_block_move(self):
        self.assertFalse(has_nonstack_block_move(""))


class GuardedReturnSectionTests(unittest.TestCase):
    """A conditional `bxCC lr` guard means the original branched; the prompt must teach the
    memory barrier that stops clang 4.0.1 from predicating the guarded body away."""

    GUARD = ("## disassembly\n\n"
             "    6013f6d4  0020a0e1  cpy     r2, r0\n"
             "    6013f6dc  070051e3  cmp     r1, #0x7\n"
             "    6013f6e0  1eff2f81  bxhi    lr\n")

    def test_conditional_return_is_detected(self):
        self.assertTrue(has_guarded_return(self.GUARD))
        for cond in ("bxeq", "bxne", "bxgt", "bxlt", "bxcs", "bxcc", "bxge", "bxle"):
            self.assertTrue(has_guarded_return(
                f"    60010000  e12fff1e  {cond}    lr\n"), cond)

    def test_a_plain_return_is_not_a_guarded_return(self):
        self.assertFalse(has_guarded_return("    60010000  e12fff1e  bx      lr\n"))
        self.assertFalse(has_guarded_return(""))
        self.assertFalse(has_guarded_return("    60010000  e12fff1e  pop     {r4,pc}\n"))

    def test_guidance_forbids_asm_only_when_a_guard_is_present(self):
        self.assertNotIn("guarded body", build_prompt(entry(), ""))
        prompt = build_prompt(entry(), self.GUARD)
        self.assertIn("predicate a small guarded body", prompt)
        self.assertIn("Do NOT try to win those bytes with inline assembly", prompt)
        self.assertNotIn('asm volatile("" ::: "memory")', prompt)


class MaskForAddressSectionTests(unittest.TestCase):
    """`bfc` on a loaded pointer used as a base: the masked value IS the base, so the prompt
    must push pointer arithmetic (integer math makes clang reorder `add` before `bfc`)."""

    BODY = ("## disassembly\n\n"
            "    608857e4  7c0d90e5  ldr     r0, [r0,#0xd7c]\n"
            "    608857e8  1f00c3e7  bfc     r0, #0x0, #0x4\n"
            "    608857ec  130a90ed  vldr.32 s0, [r0,#0x4c]\n")

    def test_mask_used_as_an_address_is_detected(self):
        self.assertTrue(has_mask_for_address(self.BODY))

    def test_a_mask_not_used_as_an_address_is_ignored(self):
        self.assertFalse(has_mask_for_address(
            "    60010000  e7c3001f  bfc     r0, #0x0, #0x4\n"
            "    60010004  e12fff1e  bx      lr\n"))
        self.assertFalse(has_mask_for_address(""))

    def test_guidance_names_pointer_arithmetic_only_when_needed(self):
        self.assertNotIn("clear its low bits", build_prompt(entry(), ""))
        self.assertIn("clear its low bits", build_prompt(entry(), self.BODY))


class TypedLoadGuidanceTests(unittest.TestCase):
    def test_the_memcpy_trap_is_always_warned_against(self):
        prompt = build_prompt(entry(), "")
        self.assertIn("__builtin_memcpy", prompt)
        self.assertIn("TYPED pointer", prompt)


class InlineAssemblyRuleTests(unittest.TestCase):
    """Hand-written instructions can never match compiled C++, so the rule is enforced on the
    candidate, not just stated. Only a declarator symbol binding is allowed; the empty barrier is
    rejected too, because it was being used to fabricate branches 4.0.1 if-converts."""

    def test_the_empty_barrier_is_rejected(self):
        for src in ('extern "C" int f(int *p) {\n'
                    '    int r = 0;\n'
                    '    if (p) { asm volatile("" ::: "memory"); r = *p; }\n'
                    '    return r;\n}\n',
                    'asm volatile("");',
                    '__asm__ volatile("" ::: "memory");',
                    'asm volatile("" ::: "memory");'):
            self.assertIsNotNone(asm_violation(src), src)

    def test_a_symbol_binding_is_allowed(self):
        self.assertIsNone(asm_violation(
            'extern "C" void reconstructed(void) asm("weird.name");'))

    def test_hand_written_instructions_are_rejected(self):
        for src in ('asm volatile("mov r0, #0");',
                    '__asm__ __volatile__("ldr r0, [r1]");',
                    'asm("bx lr");',
                    'asm volatile("nop" ::: "memory");'):
            self.assertIsNotNone(asm_violation(src), src)

    def test_the_violation_reports_the_offending_construct(self):
        self.assertIn("nop", asm_violation('asm volatile("nop");'))

    def test_ordinary_code_has_no_violation(self):
        for src in ('extern "C" int f(int *p) { return *p; }',
                    'struct S { char pad[8]; int v; };', ""):
            self.assertIsNone(asm_violation(src), src)

    def test_the_prompt_states_the_ban(self):
        prompt = build_prompt(entry(), "")
        self.assertIn("is rejected", prompt)
        self.assertNotIn('asm volatile("" ::: "memory")', prompt)
        self.assertIn("Never write inline assembly", SYSTEM)
        self.assertIn("asm", SYSTEM)


class BodyLengthFeedbackTests(unittest.TestCase):
    """A too-long body must say so: the diff words only cover the reference prefix, so
    without the sizes the model cannot see the surplus instruction it has to delete."""

    def test_a_longer_body_says_how_many_bytes_too_long(self):
        fb = Feedback("mismatch", status="body-length", diff_count=10,
                      diff_words=[{"offset": 0, "got": "7c1d90e5", "want": "7c0d90e5"}],
                      compiled_body=20, expected_body=16)
        text = feedback_section(entry(), "", fb)
        self.assertIn("20 B", text)
        self.assertIn("16 B", text)
        self.assertIn("4 BYTES TOO LONG", text)
        self.assertIn("1 instruction(s) too many", text)

    def test_a_shorter_body_is_reported_as_too_short(self):
        fb = Feedback("mismatch", status="body-length", diff_count=4,
                      compiled_body=24, expected_body=28)
        self.assertIn("4 BYTE(S) TOO SHORT", feedback_section(entry(), "", fb))

    def test_sizes_are_parsed_from_the_gate_output(self):
        record = {"outcome": "mismatch", "gate_status": "body-length", "diff_count": 10,
                  "gate_output": "compiled 20 B, original 16 B\n"}
        fb = feedback_from_record(record, Path("/nonexistent"))
        self.assertEqual((fb.compiled_body, fb.expected_body), (20, 16))


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

    def test_gate_argv_omits_the_extent_when_it_is_unknown(self):
        # An unavailable extent is omitted only so the gate can fail closed as missing-body.
        argv = gate_argv(layout(Path("/r/src")), entry(), None)
        self.assertNotIn("--body", argv)

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

    def test_skip_attempted_drops_entries_that_already_drew_their_budget(self):
        # --attempts is per run, so without this a never-matching entry stays at the front.
        entries = [entry(addr="60000024"), entry(addr="60000f8c")]
        nxt = select_next(entries, self.lay, skip_existing=True, done=set(),
                          attempted={("main", "60000024"): 9}, skip_attempted=4)
        self.assertEqual(nxt["addr"], "60000f8c")

    def test_skip_attempted_keeps_entries_under_the_budget(self):
        entries = [entry(addr="60000024")]
        nxt = select_next(entries, self.lay, skip_existing=True, done=set(),
                          attempted={("main", "60000024"): 2}, skip_attempted=4)
        self.assertEqual(nxt["addr"], "60000024")

    def test_unset_skip_attempted_changes_nothing(self):
        entries = [entry(addr="60000024")]
        nxt = select_next(entries, self.lay, skip_existing=True, done=set(),
                          attempted={("main", "60000024"): 99})
        self.assertEqual(nxt["addr"], "60000024")

    def test_from_bank_orders_closest_first_not_by_address(self):
        entries = [entry(addr="60000024"), entry(addr="60000f8c")]
        bank = {("main", "60000024"): [0, 9], ("main", "60000f8c"): [0, 1]}
        nxt = select_next(entries, self.lay, skip_existing=True, done=set(), bank=bank)
        self.assertEqual(nxt["addr"], "60000f8c")

    def test_from_bank_drops_entries_not_in_the_bank(self):
        entries = [entry(addr="60000024"), entry(addr="60000f8c")]
        bank = {("main", "60000024"): [0, 4]}
        nxt = select_next(entries, self.lay, skip_existing=True, done=set(), bank=bank)
        self.assertEqual(nxt["addr"], "60000024")
        done = {("main", "60000024")}
        self.assertIsNone(select_next(entries, self.lay, skip_existing=True, done=done,
                                      bank=bank))

    def test_from_bank_honours_the_length_and_divergence_bounds(self):
        entries = [entry(addr="60000024"), entry(addr="60000f8c")]
        bank = {("main", "60000024"): [4, 0], ("main", "60000f8c"): [0, 7]}
        self.assertIsNone(select_next(entries, self.lay, skip_existing=True, done=set(),
                                      bank=bank, bank_max_len_delta=0,
                                      bank_max_divergences=3))
        nxt = select_next(entries, self.lay, skip_existing=True, done=set(), bank=bank,
                          bank_max_len_delta=0, bank_max_divergences=8)
        self.assertEqual(nxt["addr"], "60000f8c")

    def test_max_tier_drops_relocated_entries(self):
        # tier 2 (calls out / pool reference) can never match the raw-byte gate.
        entries = [entry(addr="60000024"), entry(addr="60000f8c")]
        tiers = {("main", "60000024"): (2, 40), ("main", "60000f8c"): (0, 12)}

        def tier_key(e):
            return tiers[(e["module"], e["addr"])]

        nxt = select_next(entries, self.lay, skip_existing=True, done=set(),
                          tier_key=tier_key, max_tier=0)
        self.assertEqual(nxt["addr"], "60000f8c")
        self.assertIsNone(select_next(entries, self.lay, skip_existing=True,
                                      done={("main", "60000f8c")},
                                      tier_key=tier_key, max_tier=0))

    def test_unset_max_tier_keeps_relocated_entries(self):
        entries = [entry(addr="60000024")]
        nxt = select_next(entries, self.lay, skip_existing=True, done=set(),
                          tier_key=lambda e: (2, 40))
        self.assertEqual(nxt["addr"], "60000024")

    def test_matchable_drops_bodies_the_gate_cannot_verify(self):
        # Branch-only bodies are matchable now; pool/ADR bodies are not.
        entries = [entry(addr="60000024"), entry(addr="60000f8c")]
        ok = {("main", "60000024"): False, ("main", "60000f8c"): True}

        def matchable(e):
            return ok[(e["module"], e["addr"])]

        nxt = select_next(entries, self.lay, skip_existing=True, done=set(),
                          matchable=matchable)
        self.assertEqual(nxt["addr"], "60000f8c")
        self.assertIsNone(select_next(entries, self.lay, skip_existing=True,
                                      done={("main", "60000f8c")}, matchable=matchable))


class BankPrioritiesTests(unittest.TestCase):
    """``--from-bank`` reads the bank, keeping only records comparable under the current pin."""

    def test_keeps_current_pin_records_and_drops_others(self):
        with tempfile.TemporaryDirectory() as tmp:
            lay = Layout(ledger=Path(tmp) / "ledger.tsv", inventory=Path(tmp) / "inv",
                         nso=Path(tmp) / "nso", context=Path(tmp) / "ctx",
                         src_root=Path(tmp) / "src", build_config=Path(tmp) / "bc",
                         toolchain=Path(tmp) / "tc", work=Path(tmp) / "work")
            lay.toolchain.write_text("{\n  \"clang\": \"5.0.1\"\n}\n")
            pin = nearmiss.eval_pin(lay.toolchain)
            bank = nearmiss.empty_bank()
            nearmiss.upsert(bank, "main", "60000024", [0, 1], pin)
            nearmiss.upsert(bank, "main", "60000f8c", [0, 2], "old-pin")
            nearmiss.save_bank(bank_path(lay), bank)
            self.assertEqual(bank_priorities(lay), {("main", "60000024"): [0, 1]})

    def test_missing_bank_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            lay = Layout(ledger=Path(tmp) / "ledger.tsv", inventory=Path(tmp) / "inv",
                         nso=Path(tmp) / "nso", context=Path(tmp) / "ctx",
                         src_root=Path(tmp) / "src", build_config=Path(tmp) / "bc",
                         toolchain=Path(tmp) / "tc", work=Path(tmp) / "work")
            self.assertEqual(bank_priorities(lay), {})


class AttemptedCountsTests(unittest.TestCase):
    """The cross-run attempt tally that ``--skip-attempted`` filters on."""

    def test_counts_attempts_per_entry_across_the_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            lay = layout(Path(tmp) / "src", work=Path(tmp) / "work")
            store = attempt_store(lay)
            for addr in ("60000024", "60000024", "60000f8c"):
                attempts.append(store, {"module": "main", "addr": addr,
                                        "name": f"func_{addr}", "outcome": "mismatch"})
            self.assertEqual(attempted_counts(lay),
                             {("main", "60000024"): 2, ("main", "60000f8c"): 1})

    def test_missing_log_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(attempted_counts(layout(Path(tmp) / "src",
                                                     work=Path(tmp) / "work")), {})


class PromptFingerprintTests(unittest.TestCase):
    def test_deterministic_and_short(self):
        self.assertEqual(prompt_fingerprint("abc"), prompt_fingerprint("abc"))
        self.assertEqual(len(prompt_fingerprint("abc")), 16)

    def test_changes_with_input(self):
        self.assertNotEqual(prompt_fingerprint("a"), prompt_fingerprint("b"))


class _FakeModel:
    """Stands in for the HTTP client: returns a fixed candidate.

    Carries the same client-side attributes ``run`` fingerprints (endpoint, requested
    model name, decoding parameters, pricing) so the record fields can be asserted.
    """

    def __init__(self, text='extern "C" int func_601a72e4() { return 0; }',
                 finish_reason="", *, model="fake-model", endpoint="http://fake.local:1/v1",
                 temperature=None, max_tokens=None, seed=None, reasoning_effort=None,
                 pricing=None, system_fingerprint=""):
        self.text = text
        self.finish_reason = finish_reason
        self.model = model
        self.endpoint = endpoint
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.reasoning_effort = reasoning_effort
        self.pricing = pricing
        self.system_fingerprint = system_fingerprint

    def complete(self, prompt, *, system=None):
        return Namespace(text=self.text, model="fake", prompt_tokens=1,
                         completion_tokens=2, latency_s=0.0,
                         finish_reason=self.finish_reason, reasoning="",
                         reasoning_tokens=None,
                         system_fingerprint=self.system_fingerprint)


def fake_gate(rc: int, status: str, diff_count: int, cand_len: int, diff_words=None,
              gate_version="bytegate/test"):
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
                "has_reloc": False, "gate_version": gate_version}))
        return rc, f">>> {status.upper()}"
    return _run


class TruncatedTests(unittest.TestCase):
    """Recognising a reply that hit the output cap before answering."""

    def completion(self, **kw):
        base = dict(finish_reason="", completion_tokens=100)
        base.update(kw)
        return Namespace(**base)

    def test_length_finish_reason_is_truncation(self):
        self.assertTrue(truncated(self.completion(finish_reason="length"), None))

    def test_max_tokens_finish_reason_is_truncation(self):
        self.assertTrue(truncated(self.completion(finish_reason="max_tokens"), None))

    def test_reaching_the_cap_without_a_reason_is_truncation(self):
        model = Namespace(max_tokens=12000)
        self.assertTrue(truncated(self.completion(completion_tokens=12000), model))

    def test_a_normal_stop_is_not_truncation(self):
        model = Namespace(max_tokens=12000)
        self.assertFalse(truncated(self.completion(finish_reason="stop"), model))
        self.assertFalse(truncated(self.completion(completion_tokens=11999), model))

    def test_no_cap_and_no_reason_is_not_truncation(self):
        self.assertFalse(truncated(self.completion(completion_tokens=999999), None))


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
        self._gate_body = mock.patch("run.gate_body",
                                     side_effect=lambda _raw, body, _partition: body)
        self._gate_body.start()
        self.addCleanup(self._gate_body.stop)
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

    def test_max_tokens_truncation_is_reported_as_truncated(self):
        # A reasoning model that spends the whole budget leaves content empty:
        # finish_reason="length" is the signal, and retrying it only re-pays the cost.
        with mock.patch("run.run_subprocess", new=fake_gate(0, "match", 0, 60)):
            outcome = process(entry(), [entry()], self.lay, self.args,
                              _FakeModel("", finish_reason="length"))
        self.assertEqual(outcome, "truncated")
        self.assertFalse(self.draft.exists())
        self.assertEqual(self.log(), [])

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

    def test_attempt_records_the_experiment_fingerprint(self):
        # Everything a benchmark needs to reproduce or compare this attempt, straight from
        # the record: who answered, how it was asked, what judged it, what it cost.
        model = _FakeModel(temperature=0.2, seed=7, max_tokens=12000,
                           pricing={"input_per_mtok": 2.0, "output_per_mtok": 10.0},
                           system_fingerprint="fp_test123")
        with mock.patch("run.run_subprocess", new=fake_gate(1, "mismatch", 3, 58)):
            process(entry(), [entry()], self.lay, self.args, model)
        record = self.log()[0]
        self.assertEqual(record["kind"], "plain")
        self.assertEqual(record["provider"], "http://fake.local:1/v1")
        self.assertEqual(record["requested_model"], "fake-model")
        self.assertEqual(record["model"], "fake")            # the server-reported name
        self.assertEqual(record["system_fingerprint"], "fp_test123")
        self.assertEqual(record["decoding"], {"temperature": 0.2, "seed": 7,
                                              "max_tokens": 12000})
        self.assertIsNone(record["finish_reason"])          # the fake server reports none
        # 1 prompt tok @ $2/M + 2 completion tok @ $10/M
        self.assertAlmostEqual(record["cost_usd"], 22.0 / 1_000_000)
        self.assertEqual(record["bundle_sha256"],
                         prompt_fingerprint("# bundle: func_601a72e4\n"))
        want_tc = hashlib.sha256(b'{"clang": "clang"}').hexdigest()[:16]
        self.assertEqual(record["toolchain_sha256"], want_tc)
        self.assertEqual(record["gate_version"], "bytegate/test")

    def test_no_cost_is_recorded_without_a_pricing_table(self):
        with mock.patch("run.run_subprocess", new=fake_gate(1, "mismatch", 3, 58)):
            process(entry(), [entry()], self.lay, self.args, _FakeModel())
        self.assertNotIn("cost_usd", self.log()[0])

    def test_retry_records_kind_retry(self):
        words = [{"offset": 0, "got": "5c1080e5", "want": "170a80ed"}]
        fb = Feedback("mismatch", status="mismatch", diff_count=3, diff_words=words)
        with mock.patch("run.run_subprocess", new=fake_gate(1, "mismatch", 3, 58)):
            process(entry(), [entry()], self.lay, self.args, _FakeModel(), feedback=fb)
        self.assertEqual(self.log()[0]["kind"], "retry")

    def test_template_attempt_records_no_model_fingerprint(self):
        # A template hit makes no model call and builds no bundle: the model-side fields
        # stay absent, while the toolchain/gate identity of the judging rule is recorded.
        self.args.body = 4
        with mock.patch("run.run_subprocess", new=fake_gate(0, "match", 0, 4)):
            outcome = process(entry(), [entry()], self.lay, self.args, None,
                              raw_text=self._template_text())
        self.assertEqual(outcome, "match")
        record = self.log()[0]
        self.assertEqual(record["kind"], "plain")
        self.assertEqual(record["model"], "template")
        for field in ("provider", "requested_model", "decoding", "finish_reason"):
            self.assertNotIn(field, record)
        self.assertIsNone(record["bundle_sha256"])
        self.assertEqual(record["gate_version"], "bytegate/test")


class RepairPromptTests(unittest.TestCase):
    """Repair mode's prompt: the usual task plus a minimal-edit instruction and the
    ``UNREACHABLE`` escape, after the previous translation unit."""

    def _report(self, diff=8):
        return {"ok": False, "status": "mismatch", "cand_len": 60, "ref_len": 60,
                "diff_count": diff,
                "diff_words": [{"offset": 0, "got": "5c1080e5", "want": "170a80ed"}]}

    def test_plain_prompts_have_no_repair_instruction(self):
        self.assertNotIn("REPAIR pass", build_prompt(entry(), "B"))
        fb = Feedback("mismatch", status="mismatch", diff_count=8)
        self.assertNotIn("REPAIR pass", build_prompt(entry(), "B", fb))

    def test_repair_prompt_asks_for_a_minimal_edit(self):
        prompt = repair_prompt(entry(), "B", "SRC", self._report())
        self.assertIn("REPAIR pass", prompt)
        self.assertIn("SMALLEST edit", prompt)
        self.assertIn("UNREACHABLE", prompt)
        self.assertIn("SRC", prompt)                    # the previous TU is included
        self.assertIn("0x0", prompt)                     # the diff row

    def test_the_repair_instruction_comes_last(self):
        prompt = repair_prompt(entry(), "B", "SRC", self._report())
        self.assertGreater(prompt.index("REPAIR pass"), prompt.index("--- end ---"))

    def test_a_compile_failure_prompt_quotes_the_compiler(self):
        prompt = repair_prompt(entry(), "B", "SRC", None, "error: expected ';'")
        self.assertIn("did not compile", prompt)
        self.assertIn("expected ';'", prompt)


class _SeqModel:
    """A model that returns the scripted replies in order."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.prompts: list[str] = []
        # Client-side attributes the record fingerprints (as the real HttpModel has).
        self.model = "fake-model"
        self.endpoint = "http://fake.local:1/v1"
        self.temperature = None
        self.max_tokens = None
        self.seed = None
        self.reasoning_effort = None
        self.pricing = None

    def complete(self, prompt, *, system=None):
        self.prompts.append(prompt)
        text = self.replies.pop(0) if self.replies else ""
        return Namespace(text=text, model="fake", prompt_tokens=1, completion_tokens=2,
                         latency_s=0.0, finish_reason="stop", reasoning="",
                         reasoning_tokens=None, system_fingerprint="")


def fake_gate_seq(verdicts):
    """A ``run_subprocess`` stand-in returning scripted ``(rc, status, diff, cand_len)``."""
    pending = list(verdicts)

    def _run(argv):
        rc, status, diff_count, cand_len = pending.pop(0)
        report = Path(argv[argv.index("--report") + 1])
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({
            "module": "main", "addr": "601a72e4", "name": "func_601a72e4",
            "ok": rc == 0, "status": status, "body": 60, "partition": 1368,
            "cand_len": cand_len, "ref_len": 60, "diff_count": diff_count,
            "first_diff": 0 if diff_count else None, "diff_words": [],
            "has_reloc": False, "gate_version": "bytegate/test"}))
        return rc, f">>> {status.upper()}"

    return _run


class ProcessRepairTests(unittest.TestCase):
    """One repair session, with the gate and model stubbed out."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        root = Path(self._dir.name)
        md = root / "ctx" / "main" / "601a72e4.md"
        md.parent.mkdir(parents=True)
        md.write_text("# bundle: func_601a72e4\n")
        inv = root / "inventory.tsv"
        inv.write_text("601a72e4\tfunction\t60\tFUN\n")
        tc = root / "toolchain.json"
        tc.write_text('{"clang": "clang"}')
        self.lay = Layout(ledger=Path("/ledger"), inventory=inv, nso=Path("/nso"),
                          context=root / "ctx", src_root=root / "src",
                          build_config=Path("/bc"), toolchain=tc, work=root / "work")
        self.args = Namespace(body=None, rebuild=False, dry_run=False, force=False,
                              repair_rounds=4, repair_seeds={("main", "601a72e4"):
                                                             ("SEED", 7)})
        self._gate_body = mock.patch("run.gate_body",
                                     side_effect=lambda _raw, body, _partition: body)
        self._gate_body.start()
        self.addCleanup(self._gate_body.stop)
        self.draft = self.lay.src_root / "main" / "func_601a72e4.cpp"

    def tearDown(self):
        self._dir.cleanup()

    def log(self) -> list[dict]:
        return attempts.read_attempts(attempt_store(self.lay) / "log.jsonl")

    def bank_best(self) -> dict | None:
        bank = nearmiss.load_bank(bank_path(self.lay))
        return bank["records"].get("main:601a72e4")

    def test_a_seed_that_already_matches_is_banked_without_asking(self):
        model = _SeqModel([])
        with mock.patch("run.run_subprocess", new=fake_gate_seq([(0, "match", 0, 60)])):
            outcome = process_repair(entry(), [entry()], self.lay, self.args, model)
        self.assertEqual(outcome, "match")
        self.assertEqual(model.prompts, [])
        self.assertEqual(self.draft.read_text(), "SEED")
        self.assertEqual(self.log()[0]["source"], "repair")
        self.assertIsNone(self.bank_best())

    def test_repair_records_carry_the_fingerprint(self):
        # Even the seed's gate round (no model call yet) is a recorded attempt: kind and
        # judging identity are known, the model-side usage fields are not.
        model = _SeqModel([])
        with mock.patch("run.run_subprocess", new=fake_gate_seq([(0, "match", 0, 60)])):
            process_repair(entry(), [entry()], self.lay, self.args, model)
        record = self.log()[0]
        self.assertEqual(record["kind"], "repair")
        self.assertEqual(record["repair_seed"], 7)
        self.assertEqual(record["gate_version"], "bytegate/test")
        self.assertEqual(record["bundle_sha256"],
                         prompt_fingerprint("# bundle: func_601a72e4\n"))
        want_tc = hashlib.sha256(b'{"clang": "clang"}').hexdigest()[:16]
        self.assertEqual(record["toolchain_sha256"], want_tc)
        self.assertEqual(record["model"], "seed")           # gated before any model call
        self.assertIsNone(record["finish_reason"])
        self.assertNotIn("cost_usd", record)

    def test_a_closing_round_banks_the_match_and_keeps_it_in_src(self):
        model = _SeqModel(["MID", "WIN"])
        verdicts = [(1, "mismatch", 8, 60), (1, "mismatch", 4, 60), (0, "match", 0, 60)]
        with mock.patch("run.run_subprocess", new=fake_gate_seq(verdicts)):
            outcome = process_repair(entry(), [entry()], self.lay, self.args, model)
        self.assertEqual(outcome, "match")
        self.assertEqual(self.draft.read_text(), "WIN")
        self.assertEqual([r["source"] for r in self.log()], ["repair"] * 3)
        self.assertEqual([r["parent"] for r in self.log()], [None, 1, 2])
        self.assertEqual(len(model.prompts), 2)
        banked = self.bank_best()          # only the two misses are banked, the best is 8
        assert banked is not None
        self.assertEqual(banked["closeness"], [0, 4])

    def test_a_non_improving_reply_is_discarded_and_src_stays_clean(self):
        model = _SeqModel(["WORSE1", "WORSE2"])
        verdicts = [(1, "mismatch", 8, 60), (1, "mismatch", 20, 60),
                    (1, "mismatch", 16, 60)]
        with mock.patch("run.run_subprocess", new=fake_gate_seq(verdicts)):
            outcome = process_repair(entry(), [entry()], self.lay, self.args, model)
        self.assertEqual(outcome, "mismatch")
        self.assertFalse(self.draft.exists())
        banked = self.bank_best()
        assert banked is not None
        self.assertEqual(banked["closeness"], [0, 8])   # the seed, not the wandering edits

    def test_unreachable_stops_the_session(self):
        model = _SeqModel(["UNREACHABLE"])
        with mock.patch("run.run_subprocess", new=fake_gate_seq([(1, "mismatch", 8, 60)])):
            outcome = process_repair(entry(), [entry()], self.lay, self.args, model)
        self.assertEqual(outcome, "mismatch")
        self.assertEqual(len(self.log()), 1)            # the seed only; the sentinel is not gated
        self.assertFalse(self.draft.exists())

    def test_inline_assembly_in_a_repair_reply_is_rejected_before_the_gate(self):
        model = _SeqModel(['asm volatile("nop");', "WIN"])
        verdicts = [(1, "mismatch", 8, 60), (0, "match", 0, 60)]
        with mock.patch("run.run_subprocess", new=fake_gate_seq(verdicts)):
            outcome = process_repair(entry(), [entry()], self.lay, self.args, model)
        self.assertEqual(outcome, "match")
        self.assertEqual(len(self.log()), 2)            # rejected reply recorded nothing
        self.assertEqual(self.draft.read_text(), "WIN")

    def test_no_banked_candidate_is_an_error(self):
        self.args.repair_seeds = {}
        with mock.patch("run.bank_seed", return_value=None):
            outcome = process_repair(entry(), [entry()], self.lay, self.args, None)
        self.assertEqual(outcome, "error")
        self.assertFalse(self.draft.exists())

    def test_a_transport_error_mid_session_leaves_no_draft(self):
        class Boom:
            def complete(self, prompt, *, system=None):
                raise model.ModelError("the server went away")

        with mock.patch("run.run_subprocess", new=fake_gate_seq([(1, "mismatch", 8, 60)])):
            with self.assertRaises(model.ModelError):
                process_repair(entry(), [entry()], self.lay, self.args, Boom())
        self.assertFalse(self.draft.exists())     # src/ holds matched code only

    def test_a_merged_tu_keeps_the_best_candidate_not_the_last(self):
        entries = [entry(), entry(addr="601a72e8", group="func_601a72e4")]
        model = _SeqModel(["CLOSER", "WORSE"])
        verdicts = [(1, "mismatch", 8, 60), (1, "mismatch", 4, 60),
                    (1, "mismatch", 20, 60)]
        with mock.patch("run.run_subprocess", new=fake_gate_seq(verdicts)):
            outcome = process_repair(entry(), entries, self.lay, self.args, model)
        self.assertEqual(outcome, "mismatch")
        self.assertEqual(self.draft.read_text(), "CLOSER")


class BankSeedsTests(unittest.TestCase):
    """``--repair`` reads the banked candidate's source from the attempt store."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        root = Path(self._dir.name)
        self.lay = Layout(ledger=Path("/ledger"), inventory=Path("/inv"),
                          nso=Path("/nso"), context=Path("/ctx"), src_root=root / "src",
                          build_config=Path("/bc"), toolchain=root / "tc",
                          work=root / "work")
        self.lay.toolchain.write_text('{"clang": "clang"}')
        self.pin = nearmiss.eval_pin(self.lay.toolchain)

    def tearDown(self):
        self._dir.cleanup()

    def test_returns_the_banked_candidate_source(self):
        stored = attempts.append(attempt_store(self.lay),
                                 {"module": "main", "addr": "60000024",
                                  "name": "f", "outcome": "mismatch"},
                                 candidate_text="int f(void) { return 0; }") ["id"]
        bank = nearmiss.empty_bank()
        nearmiss.upsert(bank, "main", "60000024", [0, 4], self.pin, attempt_id=stored)
        nearmiss.save_bank(bank_path(self.lay), bank)
        seeds = bank_seeds(self.lay)
        self.assertEqual(seeds[("main", "60000024")][0].strip(),
                         "int f(void) { return 0; }")
        self.assertEqual(seeds[("main", "60000024")][1], stored)

    def test_a_record_from_another_pin_is_skipped(self):
        bank = nearmiss.empty_bank()
        nearmiss.upsert(bank, "main", "60000024", [0, 4], "old-pin", attempt_id=1)
        nearmiss.save_bank(bank_path(self.lay), bank)
        self.assertEqual(bank_seeds(self.lay), {})

    def test_a_missing_bank_is_empty(self):
        self.assertEqual(bank_seeds(self.lay), {})


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

    def test_truncation_stops_instead_of_retrying(self):
        # Every retry would spend the same max_tokens budget and return nothing again.
        calls = []

        def one(*_):
            calls.append(1)
            return "truncated"

        self.assertEqual(self._run(one), ("error", 1))
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


class DescribeWordDiffTests(unittest.TestCase):
    """The near-miss hint: raw differing hex must become an edit the model can make."""

    def test_a_condition_code_difference_names_both_conditions(self):
        # movcc r0,r1 (0x31A00001) vs movls r0,r1 (0x91A00001)
        hint = describe_word_diff("0100a031", "0100a091")
        self.assertIn("condition code", hint)
        self.assertIn("`cc`", hint)
        self.assertIn("`ls`", hint)

    def test_a_missing_writeback_is_reported(self):
        # ldr r1,[r0,r1] vs ldr r1,[r0,r1]!
        hint = describe_word_diff("011090e7", "0110b0e7")
        self.assertIn("`!`", hint)
        self.assertIn("original writes", hint)

    def test_a_missing_writeback_on_a_halfword_load_is_reported(self):
        # ldrh r2,[r0,r2] vs ldrh r2,[r0,r2]!
        self.assertIn("`!`", describe_word_diff("b22090e1", "b220b0e1"))

    def test_a_load_store_swap_is_reported(self):
        # str r1,[r0,#8] vs ldr r1,[r0,#8]
        self.assertIn("load vs store", describe_word_diff("081080e5", "081090e5"))

    def test_an_immediate_difference_is_reported(self):
        # movw r2,#0x10 vs movw r2,#0x01
        self.assertIn("immediate", describe_word_diff("102040e3", "012040e3"))

    def test_identical_words_say_nothing(self):
        self.assertEqual(describe_word_diff("0100a0e1", "0100a0e1"), "")

    def test_an_unrecognised_difference_says_nothing_rather_than_guessing(self):
        # A pure register-allocation difference (mov r1,#0 vs mov r2,#0).
        self.assertEqual(describe_word_diff("0010a0e3", "0020a0e3"), "")

    def test_malformed_input_is_tolerated(self):
        self.assertEqual(describe_word_diff("zz", "0100a091"), "")
        self.assertEqual(describe_word_diff("", ""), "")


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
