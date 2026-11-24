"""The experiment report: attribute a benchmark run's results to a variant.

Plan Batch 2. A variant is a named ``run.py --experiment`` pass over a benchmark slice
(``tools/loop/benchmark.py``) under an explicit budget. Every attempt record already carries
the experiment fingerprint (plan step 1.3 — provider/model/decoding, toolchain and gate
versions, tokens, cost); this tool aggregates those records against the frozen benchmark so
a run answers, per *Success measures*:

    unique matches (by entry, never by attempt — the metric that matters), with the
        match's source (template / model / repair) and kind;
    compile failures (clang-rejected candidates: outcome ``error`` with gate exit 3);
    exact-length near misses (the bank's closeness ``[0, d>0]`` under the current eval pin);
    repairs (``kind=repair`` attempts and the matches they produced);
    time, prompt/completion/reasoning tokens, and recorded cost (absent pricing is
        reported as "not recorded", never "free").

A match the ledger shows but no variant record produced is **matched outside the
experiment** — a re-gated candidate or a deterministic template applied by another pass —
so free conversions are never credited to the variant. ``--compare a,b`` reports the matched
set difference; an entry matched by both is attributed to the variant whose earliest
matching attempt id is lower (ids are global and time-ordered, so this is reproducible).

The variant's identity is checked: provider/requested model, decoding parameters,
toolchain hash, and gate version are collected from its records, and a mixture is flagged —
records from two configurations under one name make comparisons invalid.

Usage::

    python3 tools/loop/experiment.py --name v1 --variant control
    python3 tools/loop/experiment.py --name v1 --split dev --variant control --json r.json
    python3 tools/loop/experiment.py --name v1 --compare control,align-asm
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))
sys.path.insert(0, str(REPO / "tools" / "loop"))

import attempts
import benchmark
import nearmiss
from ledgerlib import read_entries


# --- pure aggregation (unit-tested) ---------------------------------------------------

def filter_records(records: list[dict], keys: set[tuple[str, str]],
                   variant: str | None) -> list[dict]:
    """The benchmark-scoped records for one variant (``None`` = every experiment tag)."""
    out = []
    for r in records:
        if (r.get("module"), r.get("addr")) not in keys:
            continue
        if variant is not None and r.get("experiment") != variant:
            continue
        out.append(r)
    return out


def identity_of(records: list[dict]) -> dict:
    """The distinct identity fields across a variant's records, flagging a mixture."""
    fields = ("provider", "requested_model", "model", "toolchain_sha256", "gate_version")
    values = {f: sorted({str(r[f]) for r in records if r.get(f) is not None}) for f in fields}
    decodings = sorted({json.dumps(r["decoding"], sort_keys=True)
                        for r in records if r.get("decoding")})
    values["decoding"] = decodings
    mixed = [f for f, v in values.items() if len(v) > 1]
    return {"values": values, "mixed": mixed}


def summarize(records: list[dict], entries: list[dict], *,
              bank_close: dict[tuple[str, str], list[int]],
              ledger_verify: dict[tuple[str, str], str]) -> dict:
    """Aggregate one variant's records over the benchmark entries (all pure).

    ``entries`` are the benchmark's per-entry dicts (``cohorts``/``split`` included),
    ``bank_close`` the current-pin closeness per key, ``ledger_verify`` each key's current
    ``verify`` value.
    """
    keys = {(e["module"], e["addr"]) for e in entries}
    by_key: dict[tuple[str, str], list[dict]] = {}
    for r in records:
        by_key.setdefault((r.get("module"), r.get("addr")), []).append(r)
    for rs in by_key.values():
        rs.sort(key=lambda r: int(r.get("id") or 0))

    matched: dict[tuple[str, str], int] = {}
    match_source: dict[tuple[str, str], str] = {}
    for key, rs in by_key.items():
        wins = [r for r in rs if r.get("outcome") == "match"]
        if wins:
            matched[key] = int(wins[0]["id"])
            match_source[key] = wins[0].get("source") or "?"

    compile_records = [r for r in records if r.get("outcome") == "error"
                       and r.get("gate_rc") == 3]
    usage_records = [r for r in records if r.get("prompt_tokens") is not None
                     or r.get("completion_tokens") is not None]

    def tokens(name: str) -> int:
        return sum(int(r.get(name) or 0) for r in usage_records)

    attempted = set(by_key)
    near_exact = sorted(k for k in attempted
                        if k in bank_close and int(bank_close[k][0]) == 0
                        and int(bank_close[k][1]) > 0)
    matched_now = {k for k in keys if ledger_verify.get(k) == "match"}
    sources = Counter(match_source.values())
    kinds = Counter(r.get("kind") or "?" for r in records)
    first_source = Counter(match_source[k] for k in matched)

    return {
        "entries_total": len(entries),
        "entries_attempted": len(attempted),
        "attempts": len(records),
        "attempts_by_kind": dict(kinds),
        "matches": {f"{m}/{a}": i for (m, a), i in sorted(matched.items())},
        "unique_matches": len(matched),
        "match_first_source": dict(sources),
        "matches_by_repair": first_source.get("repair", 0),
        "compile_failure_attempts": len(compile_records),
        "compile_failure_entries": len({(r.get("module"), r.get("addr"))
                                        for r in compile_records}),
        "exact_length_near_misses": len(near_exact),
        "latency_s": round(sum(float(r.get("latency_s") or 0.0) for r in records), 3),
        "tokens": {"prompt": tokens("prompt_tokens"), "completion": tokens("completion_tokens"),
                   "reasoning": tokens("reasoning_tokens")},
        "cost_usd": round(sum(float(r.get("cost_usd") or 0.0) for r in records), 6),
        "cost_recorded": any(r.get("cost_usd") is not None for r in records),
        "identity": identity_of(records),
        "cohorts": {tag: {"attempted": sum(1 for e in entries
                                           if tag in e["cohorts"]
                                           and (e["module"], e["addr"]) in attempted),
                          "matched": sum(1 for e in entries
                                         if tag in e["cohorts"]
                                         and (e["module"], e["addr"]) in matched)}
                    for tag in benchmark.COHORT_ORDER},
        "splits": {split: {"attempted": sum(1 for e in entries if e["split"] == split
                                            and (e["module"], e["addr"]) in attempted),
                           "matched": sum(1 for e in entries if e["split"] == split
                                          and (e["module"], e["addr"]) in matched),
                           "total": sum(1 for e in entries if e["split"] == split)}
                   for split in ("dev", "holdout")},
        "matched_outside_experiment": sorted(f"{k[0]}/{k[1]}" for k in matched_now - set(matched)),
        "unmatched": len(keys - matched_now),
    }


def compare(summaries: dict[str, dict]) -> dict:
    """The matched-set difference across named variants.

    An entry matched by several variants is attributed to the one whose earliest matching
    attempt id is lowest (ids are global and time-ordered). Keys are ``module/addr``.
    """
    sets = {name: set(s["matches"]) for name, s in summaries.items()}
    names = list(summaries)
    union: set[str] = set().union(*sets.values()) if sets else set()
    only = {}
    attributed = Counter()
    for key in sorted(union):
        holders = [n for n in names if key in sets[n]]
        if len(holders) == 1:
            only.setdefault(f"only_{holders[0]}", []).append(key)
            attributed[holders[0]] += 1
        else:
            winner = min(holders, key=lambda n: summaries[n]["matches"][key])
            attributed[winner] += 1
    for n in names:
        only.setdefault(f"only_{n}", [])
    return {"attributed": dict(attributed),
            **only}


# --- presentation ---------------------------------------------------------------------

def format_summary(name: str, s: dict, split: str) -> list[str]:
    lines = [f"variant {name!r}  (split: {split})"]
    ident = s["identity"]
    lines.append("  identity: " + ", ".join(f"{f}={v}" for f, v in ident["values"].items()))
    if ident["mixed"]:
        lines.append("  WARNING: mixed identity across records: "
                     + ", ".join(ident["mixed"]) + " — comparisons are invalid")
    lines.append(f"  entries attempted {s['entries_attempted']} of {s['entries_total']}; "
                 f"attempts {s['attempts']} {s['attempts_by_kind']}")
    lines.append(f"  unique matches {s['unique_matches']} "
                 f"(first-source {s['match_first_source'] or '{}'}) · "
                 f"matched outside experiment {len(s['matched_outside_experiment'])} · "
                 f"unmatched {s['unmatched']}")
    lines.append(f"  compile failures: {s['compile_failure_attempts']} attempts / "
                 f"{s['compile_failure_entries']} entries · "
                 f"exact-length near misses: {s['exact_length_near_misses']} entries · "
                 f"repair-produced matches: {s['matches_by_repair']}")
    cost = f"${s['cost_usd']:.4f}" if s["cost_recorded"] else "not recorded (no pricing)"
    t = s["tokens"]
    lines.append(f"  time {s['latency_s']:.0f}s · tokens {t['prompt']:,} prompt + "
                 f"{t['completion']:,} completion + {t['reasoning']:,} reasoning · cost {cost}")
    splits = ", ".join(f"{sp}: {v['matched']}/{v['attempted']} matched/attempted "
                       f"of {v['total']}" for sp, v in s["splits"].items())
    lines.append(f"  by split: {splits}")
    rows = [f"    {tag:<12} {v['attempted']:>4} attempted {v['matched']:>4} matched"
            for tag, v in s["cohorts"].items() if v["attempted"] or v["matched"]]
    if rows:
        lines.append("  cohorts:")
        lines.extend(rows)
    return lines


# --- CLI ------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="the benchmark name")
    ap.add_argument("--dir", type=Path, default=benchmark.DEFAULT_DIR)
    ap.add_argument("--store", type=Path, default=REPO / "baserom" / "work" / "attempts",
                    help="the attempt store (default baserom/work/attempts)")
    ap.add_argument("--ledger", type=Path, default=benchmark.DEFAULT_LEDGER)
    ap.add_argument("--toolchain", type=Path, default=benchmark.DEFAULT_TOOLCHAIN)
    ap.add_argument("--bank", type=Path, default=REPO / "baserom" / "work" / "nearmiss" / "bank.json")
    ap.add_argument("--variant", default=None, help="report this experiment tag")
    ap.add_argument("--compare", default=None, metavar="A,B",
                    help="compare exactly two variant tags (matched-set attribution)")
    ap.add_argument("--split", choices=("dev", "holdout", "all"), default="all",
                    help="which benchmark split to report (default all)")
    ap.add_argument("--json", type=Path, default=None, help="write the machine-readable report")
    args = ap.parse_args(argv)

    if args.variant and args.compare:
        print("error: --variant and --compare are alternatives", file=sys.stderr)
        return 2
    if args.compare:
        names = [n.strip() for n in args.compare.split(",") if n.strip()]
        if len(names) != 2:
            print("error: --compare takes exactly two variant names (a,b)", file=sys.stderr)
            return 2
    else:
        names = [args.variant] if args.variant else [None]

    try:
        doc = benchmark.load_document(args.dir, args.name)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    entries = [e for e in doc["entries"]
               if args.split == "all" or e["split"] == args.split]
    if not entries:
        print(f"error: no benchmark entries for split {args.split!r}", file=sys.stderr)
        return 2
    keys = {(e["module"], e["addr"]) for e in entries}

    try:
        records = attempts.read_attempts(args.store / "log.jsonl")
    except attempts.AttemptError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    pin = nearmiss.eval_pin(args.toolchain)
    bank = nearmiss.load_bank(args.bank)
    bank_close = {(r.get("module"), r.get("addr")): list(r["closeness"])
                  for r in bank.get("records", {}).values()
                  if r.get("pin") == pin and r.get("closeness")}
    ledger_verify = {(e["module"], e["addr"]): e["verify"]
                     for e in read_entries(args.ledger)}

    summaries = {}
    for name in names:
        scoped = filter_records(records, keys, name)
        summaries[name or "*"] = summarize(scoped, entries, bank_close=bank_close,
                                           ledger_verify=ledger_verify)

    out = {"benchmark": {"name": doc["name"], "digest": doc["digest"],
                         "inputs": doc["inputs"], "split": args.split,
                         "entries": len(entries)},
           "eval_pin": pin,
           "variants": summaries}
    if len(names) == 2:
        out["compare"] = compare(summaries)

    header = (f"benchmark {doc['name']}  digest {doc['digest']}  "
              f"({len(entries)} entries, split={args.split})  eval pin {pin}")
    print(header)
    for name, s in summaries.items():
        for line in format_summary(name, s, args.split):
            print(line)
    if len(names) == 2:
        a, b = names[0] or "*", names[1] or "*"
        cmp = out["compare"]
        print(f"compare {a} vs {b}:")
        print(f"  attributed unique matches: {cmp['attributed']}")
        for n in (a, b):
            only = cmp.get(f"only_{n}", [])
            print(f"  only {n}: {len(only)}" + (f"  ({', '.join(only)})" if only else ""))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
