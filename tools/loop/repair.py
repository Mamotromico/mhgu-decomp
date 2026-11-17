"""Repair mode: iterate on a near miss instead of resampling it.

A plain retry resends the same prompt (plus the divergence) and hopes a fresh sample lands.
That is wasteful for the one class of failure that is *almost right*: a candidate that compiles
to exactly the original body length and differs in only a handful of instructions. There the
model has already produced the right shape; what it needs is to be told precisely which
instructions are wrong and asked to change only those.

This module is that loop, and nothing else:

    seed (a banked candidate)
      gate -> already a match?  done
      while the candidate is eligible and rounds remain:
          prompt  = prompt_for(best_source, best_report)      (built by the caller)
          reply   = ask(prompt)                               (the model)
          gate    = gate(reply)                               (the byte gate)
          keep it only if it is *strictly closer* than the best so far
      return the best candidate + its report

The two rules that make it safe:

* **Monotone.** A reply is adopted only when it is strictly closer by the gate's own
  ``closeness`` (``(|cand_len - ref_len|, diff_count)`` — the same pair the near-miss bank
  ranks by). A repair that wanders off is discarded, so the loop can never end worse than the
  seed, and a fixed budget cannot be spent walking backwards.
* **The gate and the model are injected.** Every decision here is a pure function of the
  reports the caller supplies, so the whole loop is unit-tested with fakes — no clang, no
  Ghidra, no network. ``run.py`` supplies the real gate and model.

The model is given one escape hatch: if the only remaining differences are *register
allocation* (which no source shape controls), it replies ``UNREACHABLE`` and the loop stops
instead of burning the rest of the budget on an unwinnable edit.

Eligibility (:func:`eligible`):

* the seed must be a ``mismatch`` — a ``body-length`` or compile failure is a different
  function shape, not a repair;
* the compiled and reference lengths must agree (the length delta must be 0), so
  ``diff_count`` is a like-for-like comparison;
* at most ``MAX_DIFF_WORDS`` differing words (24 bytes): beyond that it is a rewrite, and a
  fresh attempt is cheaper than an incremental one.

Usage::

    python3 tools/loop/run.py --repair --limit 20
    python3 tools/loop/run.py --repair --entry 601a72e4 --repair-rounds 6
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# How many differing words (4 bytes each) are still worth an incremental edit. Past this the
# candidate is not "almost right", it is a different implementation.
MAX_DIFF_WORDS = 6

# The model's escape hatch: the remaining bytes are the original compiler's register
# allocation, which no C source shape controls.
UNREACHABLE = "UNREACHABLE"

_UNREACHABLE = re.compile(r"^\W*UNREACHABLE\b", re.I)


def is_unreachable(text: str | None) -> bool:
    """Whether a reply is the ``UNREACHABLE`` escape hatch rather than a translation unit."""
    return bool(text) and bool(_UNREACHABLE.match(text.lstrip()))


def closeness(report: dict | None) -> tuple[int, int]:
    """The gate's own closeness pair — ``(|cand_len - ref_len|, diff_count)``, lower is better.

    Kept identical to ``nearmiss.closeness`` so "closer" means the same thing in the repair
    loop as it does in the bank; a report with no comparable bytes ranks as infinitely far.
    """
    if not report:
        return (1 << 30, 1 << 30)
    cand = int(report.get("cand_len") or 0)
    ref = int(report.get("ref_len") or 0)
    return (abs(cand - ref), int(report.get("diff_count") or 0))


def strictly_closer(candidate: dict | None, best: dict | None) -> bool:
    """Whether ``candidate`` is strictly better than ``best`` (a compile failure never is)."""
    if candidate is None:
        return False
    return closeness(candidate) < closeness(best)


def eligible(report: dict | None,
             max_diff_words: int = MAX_DIFF_WORDS) -> tuple[bool, str]:
    """Whether this report is a repairable near miss; returns ``(ok, reason)``.

    ``reason`` is human-readable either way, so the driver can say why it skipped an entry
    instead of silently repairing nothing.
    """
    if report is None:
        return False, "no gate report (the candidate did not compile)"
    if report.get("ok"):
        return False, "already matches"
    status = report.get("status")
    if status != "mismatch":
        return False, (f"gate status {status!r} — only a same-length mismatch is repairable "
                       f"(a length difference is a different shape, not an edit)")
    diff = int(report.get("diff_count") or 0)
    if diff <= 0:
        return False, "no differing bytes"
    words = (diff + 3) // 4
    if words > max_diff_words:
        return False, (f"{diff} differing byte(s) (~{words} words) exceeds the "
                       f"{max_diff_words}-word repair budget")
    return True, f"{diff} differing byte(s)"


@dataclass
class RepairResult:
    """The outcome of one repair session.

    ``source`` is the **best** candidate seen (the seed when nothing improved) and ``report``
    its gate report, so the caller can keep exactly what the gate judged best. ``improved``
    distinguishes "already matched on arrival" from "a repair produced the match".
    """

    outcome: str                      # "match" | "mismatch" | "error"
    source: str | None = None
    report: dict | None = None
    rounds_used: int = 0
    improved: bool = False
    history: list = field(default_factory=list)   # closeness after each gated candidate

    @property
    def matched(self) -> bool:
        return self.outcome == "match"


def repair(seed_source: str | None, *, gate, ask, prompt_for,
           rounds: int = 4, max_diff_words: int = MAX_DIFF_WORDS, log=None) -> RepairResult:
    """Run the monotone repair loop on one entry.

    ``gate(source) -> (report|None, output)`` compiles and byte-compares a translation unit;
    ``report`` is ``None`` when it did not compile and ``output`` is the gate's text (used for
    the compile-error hint). ``ask(prompt) -> str|None`` returns the model's reply.
    ``prompt_for(source, report, output) -> str`` builds the next prompt from the current best.

    Stops early on: a match, an ineligible candidate (the length moved, it got too far, the
    model said ``UNREACHABLE``), an empty reply, or the round budget. The result always carries
    the best candidate seen, so a failed repair still leaves the bank no worse off.
    """
    log = log or (lambda _msg: None)
    if not seed_source:
        return RepairResult("error", None, None, 0, False)

    report, output = gate(seed_source)
    result = RepairResult("match" if (report and report.get("ok")) else "error",
                          seed_source, report, 0, False, [closeness(report)])
    if report is not None:
        result.outcome = "match" if report.get("ok") else "mismatch"
    if result.outcome != "mismatch":
        return result

    for _ in range(max(1, rounds)):
        ok, why = eligible(report, max_diff_words)
        if not ok:
            log(f"    repair: stopping — {why}")
            break
        prompt = prompt_for(seed_source, report, output)
        reply = ask(prompt)
        result.rounds_used += 1
        if not reply or not reply.strip():
            log("    repair: empty reply; stopping")
            break
        if is_unreachable(reply):
            log("    repair: the model reported UNREACHABLE (register allocation only)")
            break
        candidate, output = gate(reply)
        result.history.append(closeness(candidate))
        if candidate is None:
            log("    repair: candidate did not compile; retrying")
            continue
        if candidate.get("ok"):
            result.outcome, result.source, result.report = "match", reply, candidate
            result.improved = True
            return result
        if strictly_closer(candidate, report):
            before = closeness(report)
            report, seed_source = candidate, reply
            result.source, result.report, result.improved = reply, candidate, True
            log(f"    repair: closer {list(before)} -> {list(closeness(candidate))}")
        else:
            log(f"    repair: not closer ({list(closeness(candidate))} vs "
                f"{list(closeness(report))}); keeping the best")
    return result
