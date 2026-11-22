"""Re-gate the already-matched corpus under a candidate toolchain profile.

The ledger marks every reconstruction with ``verify=match``, but that verdict was
produced by *some* compiler profile. Changing the pin (see ``AGENTS.md`` →
*Compiler pin revision: clang 4.0.1*) is only safe if we know exactly which
already-matched functions stop matching — a *regression* — before the new profile
becomes the default.

This tool answers that question: it selects every ``kind=function, verify=match``
entry, recompiles its existing ``src/<module>/<group>.cpp`` with the candidate
profile, re-runs the **same** byte gate (``tools/ledger/bytegate.py``), and reports
a status count plus the concrete regression list (with the differing instructions).
It never edits the ledger or ``src/``; it only compiles into a git-ignored work
directory.

The default run loads ``config/main/revalidate-known-residuals.tsv``: the reviewed
clang 4.0.1 compiler residuals. Exact ``(addr, status, diff_count)`` failures are
reported as accepted `known-residual`s; changed residuals, resolved residuals, missing
baseline entries, and unexplained failures all fail the run. Pass
``--known-residuals ""`` for a strict comparison with no accepted failures.

Faithfulness to how functions were originally matched
------------------------------------------------------
The loop asserts the inventory instruction span extended through every referenced literal-pool
word (``run.gate_body``). This tool derives the same extent from the reference bytes, so
partition/padding differences are not false regressions and a matching prefix is never accepted.

Reference bytes come straight from the NSO (``complexity.load_text``), written once
as a ``.text_<start>.bin`` and handed to the gate via ``--ref-bin`` — no Ghidra run
per function.

Usage::

    # Re-gate the whole matched corpus under the 4.0.1 profile
    python3 tools/ledger/revalidate.py

    # Use an extracted compiler without rebuilding the devcontainer
    python3 tools/ledger/revalidate.py --clang /tmp/clangv/.../bin/clang

    # Machine-readable + CI-friendly (exit 1 on any regression)
    python3 tools/ledger/revalidate.py --report baserom/work/revalidate.json \
        --tsv baserom/work/revalidate.tsv

    # A subset, in parallel
    python3 tools/ledger/revalidate.py --module main --limit 200 --jobs 4

Exit codes::

    0  every selected entry matches, or every failure exactly matches the known baseline
    1  one or more regressions, changed/resolved residuals, or missing baseline entries
    2  usage / setup error (missing ledger, NSO, or compiler)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

class SetupError(Exception):
    """A usage/setup problem (missing profile, compiler, or NSO) — exit code 2."""


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))
sys.path.insert(0, str(REPO / "tools" / "loop"))

import complexity
from bundle import BundleError, parse_inventory, resolve_body
from ledgerlib import read_entries

BYTEGATE = REPO / "tools" / "ledger" / "bytegate.py"
DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_SRC_ROOT = REPO / "src"
DEFAULT_TOOLCHAIN = REPO / "config" / "toolchain.json"
DEFAULT_NSO = REPO / "baserom" / "main.nso"
DEFAULT_INVENTORY = REPO / "baserom" / "work" / "inventory" / "inventory.tsv"
DEFAULT_BUILD_CONFIG = REPO / "config" / "build.json"
DEFAULT_KNOWN_RESIDUALS = REPO / "config" / "main" / "revalidate-known-residuals.tsv"
DEFAULT_WORK = REPO / "baserom" / "work" / "revalidate"
REF_BASE = 0x60000000


# --- pure helpers (unit-tested) -------------------------------------------------------

def selected(entries: list[dict], *, module: str | None = None,
             limit: int = 0) -> list[dict]:
    """The entries to re-gate: every matched function, optionally one module/limit.

    Ordered by the ledger's own ``(module, addr)`` so a run is deterministic and two
    profiles can be diffed entry-for-entry.
    """
    rows = [e for e in entries
            if e.get("kind") == "function" and e.get("verify") == "match"
            and (module is None or e.get("module") == module)]
    rows.sort(key=lambda e: (e["module"], e["addr"]))
    return rows if limit <= 0 else rows[:limit]


def summarize(results: list[dict]) -> dict[str, int]:
    """Count results, honouring the explicit residual classification when present."""
    counts: dict[str, int] = {}
    for r in results:
        key = r.get("classification")
        if key is None:
            key = "match" if r.get("ok") else str(r.get("status") or "error")
        counts[key] = counts.get(key, 0) + 1
    return counts


def regressions(results: list[dict]) -> list[dict]:
    """The results that are *not* a match, in a compact, report-friendly shape."""
    out = []
    for r in results:
        if r.get("ok"):
            continue
        out.append({
            "module": r.get("module"),
            "addr": r.get("addr"),
            "name": r.get("name"),
            "status": r.get("status") or "error",
            "diff_count": r.get("diff_count"),
            "diff_words": r.get("diff_words") or [],
            "rc": r.get("rc"),
            "detail": r.get("detail", ""),
        })
    return out


def read_known_residuals(path: Path) -> dict[tuple[str, str], dict]:
    """Parse the reviewed known-residual baseline.

    The baseline pins each accepted compiler residual to the gate ``status`` and
    ``diff_count`` observed under the accepted compiler profile. It deliberately
    stores no instruction bytes. A same-address failure with a different status or
    divergence count is *not* accepted: that is a new regression, not evidence that
    the old residual remains unchanged.
    """
    text = Path(path).read_text()
    baseline: dict[tuple[str, str], dict] = {}
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        fields = line.split("\t")
        where = f"{path}:{lineno}"
        if [f.strip() for f in fields] == ["module", "addr", "status", "diff_count"]:
            continue
        if len(fields) != 4:
            raise ValueError(f"{where}: expected module, addr, status, diff_count")
        module, addr, status, diff_count = (f.strip() for f in fields)
        try:
            addr = f"{int(addr, 16):08x}"
        except ValueError as e:
            raise ValueError(f"{where}: addr must be a hexadecimal ledger address") from e
        if not module or not status:
            raise ValueError(f"{where}: module and status are required")
        try:
            diff_count = int(diff_count)
        except ValueError as e:
            raise ValueError(f"{where}: diff_count must be an integer") from e
        if diff_count < 0:
            raise ValueError(f"{where}: diff_count must be >= 0")
        key = (module, addr)
        if key in baseline:
            raise ValueError(f"{where}: duplicate residual {key}")
        baseline[key] = {"status": status, "diff_count": diff_count}
    return baseline


def classify_residuals(results: list[dict],
                       baseline: dict[tuple[str, str], dict] | None) -> dict:
    """Split gate results into matches, accepted residuals, and unexplained failures.

    ``known-residual`` requires an exact key, status, and divergence-count match.
    A residual that now matches is reported as ``resolved`` (a stale baseline, so the
    caller must update it deliberately); a baseline entry absent from the selected
    results is also stale. Anything else is a ``regression``.
    """
    classified: list[dict] = []
    regressions: list[dict] = []
    known: list[dict] = []
    resolved: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for result in results:
        key = (result.get("module"), result.get("addr"))
        seen.add(key)
        if result.get("ok"):
            row = {**result, "classification": "match"}
            if baseline is not None and key in baseline:
                row["classification"] = "resolved-residual"
                resolved.append(row)
            classified.append(row)
            continue

        expected = baseline.get(key) if baseline is not None else None
        exact = (expected is not None
                 and result.get("status") == expected["status"]
                 and result.get("diff_count") == expected["diff_count"])
        if exact:
            row = {**result, "classification": "known-residual"}
            known.append(row)
        else:
            row = {**result, "classification": "regression"}
            if expected is not None:
                row["expected"] = expected
            regressions.append(row)
        classified.append(row)

    missing = []
    if baseline is not None:
        for module, addr in sorted(baseline):
            if (module, addr) not in seen:
                missing.append({"module": module, "addr": addr,
                                "status": "missing", "diff_count": None,
                                "classification": "missing-residual"})

    return {"results": classified, "regressions": regressions,
            "known_residuals": known, "resolved_residuals": resolved,
            "missing_residuals": missing}


def result_from_report(entry: dict, report: dict | None, rc: int,
                       output: str = "") -> dict:
    """Normalize a gate report (or its absence) into one result record.

    A missing report means the gate never reached the comparison — a compile
    failure (rc 3) or a setup error — so it is recorded as ``error`` with the gate's
    output tail for diagnosis.
    """
    base = {"module": entry["module"], "addr": entry["addr"], "name": entry["name"],
            "rc": rc}
    if report is None:
        return {**base, "ok": False, "status": "error", "diff_count": None,
                "diff_words": [], "detail": output.strip()[-400:]}
    return {**base, "ok": bool(report.get("ok")),
            "status": report.get("status"), "diff_count": report.get("diff_count"),
            "diff_words": report.get("diff_words") or []}


def build_report(toolchain: str, clang: str, clang_version: str,
                 results: list[dict],
                 baseline: dict[tuple[str, str], dict] | None = None) -> dict:
    """The machine-readable summary written by ``--report``."""
    report = {
        "toolchain": toolchain,
        "clang": clang,
        "clang_version": clang_version,
        "total": len(results),
        "counts": summarize(results),
        "regressions": regressions(results),
    }
    if baseline is not None:
        classified = classify_residuals(results, baseline)
        report["counts"] = summarize(classified["results"])
        report["regressions"] = classified["regressions"]
        report["known_residuals"] = classified["known_residuals"]
        report["resolved_residuals"] = classified["resolved_residuals"]
        report["missing_residuals"] = classified["missing_residuals"]
    return report


def format_counts(counts: dict[str, int]) -> str:
    """One deterministic line, ``match`` first then the rest alphabetically."""
    order = sorted(counts, key=lambda k: (k != "match", k))
    return ", ".join(f"{k}={counts[k]}" for k in order)


# --- impure steps ---------------------------------------------------------------------

def resolve_clang(toolchain: dict) -> str:
    """The compiler binary a profile names, resolved to an executable path.

    A bare name resolves through ``PATH``; an absolute path must exist. This is the
    one place a missing compiler is caught, with an actionable message (rebuild the
    devcontainer, or pass ``--clang``).
    """
    name = toolchain.get("clang", "clang")
    found = shutil.which(name) if "/" not in name else (name if Path(name).exists() else None)
    if not found:
        raise SetupError(
            f"compiler not found: {name}\n"
            f"  the {Path(toolchain.get('_source', 'profile')).name} profile expects it to be "
            f"installed.\n  Rebuild the devcontainer, or point at a local build with --clang PATH.")
    return found


def clang_version(clang: str) -> str:
    try:
        out = subprocess.run([clang, "--version"], capture_output=True, text=True,
                             check=False)
        return (out.stdout or out.stderr).splitlines()[0] if (out.stdout or out.stderr) else ""
    except OSError:
        return ""


def write_ref_bin(text: bytes, work: Path) -> Path:
    """Materialise the reference ``.text`` as ``.text_<start>.bin`` for ``--ref-bin``.

    The gate's ``block_bin`` parses the start address from the filename, so the name
    is load-bearing. Writing it once is what lets every gate run skip Ghidra.
    """
    ref = work / "ref"
    ref.mkdir(parents=True, exist_ok=True)
    path = ref / f".text_{REF_BASE:08x}.bin"
    path.write_bytes(text)
    return path


def remap_include_flags(cflags: list[str], clang: str) -> list[str]:
    """Point a profile's libc++ ``-isystem`` entry at the override compiler's headers.

    ``--clang`` swaps only the binary; a profile still names the *installed* libc++
    path (e.g. ``/opt/clang-4.0.1/include/c++/v1``). When that directory does not
    exist but the override binary has a sibling ``include/c++/v1`` (an extracted
    tarball), the flag is repaired so ``<cstdint>`` et al. resolve. An installed
    profile is left untouched.
    """
    if "/" not in clang:
        return list(cflags)
    fallback = Path(clang).resolve().parent.parent / "include" / "c++" / "v1"
    if not fallback.is_dir():
        return list(cflags)
    out = list(cflags)
    for i in range(len(out) - 1):
        if out[i] == "-isystem" and out[i + 1].endswith("/include/c++/v1") \
                and not Path(out[i + 1]).is_dir():
            out[i + 1] = str(fallback)
    return out


def effective_profile(toolchain_path: Path, clang_override: str | None,
                      work: Path) -> tuple[Path, dict]:
    """Load the candidate profile, applying ``--clang`` and returning (path, data).

    The override is written to a temporary profile so the gate subprocess — which
    only accepts a path — sees it; the user's committed profile is never modified.
    Its libc++ ``-isystem`` path is repaired to match the override binary (see
    :func:`remap_include_flags`).
    """
    try:
        data = json.loads(toolchain_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise SetupError(f"bad toolchain profile {toolchain_path}: {e}")
    data["_source"] = str(toolchain_path)
    if clang_override:
        data["clang"] = clang_override
        data["cflags"] = remap_include_flags(data.get("cflags", []), clang_override)
        tmp = Path(tempfile.mkdtemp(dir=work)) / "toolchain.json"
        tmp.write_text(json.dumps(data, indent=2))
        return tmp, data
    return toolchain_path, data


def gate_one(entry: dict, *, toolchain: Path, src_root: Path, ledger: Path,
             nso: Path, build_config: Path, ref_bin: Path, body: int | None,
             build_dir: Path, report_dir: Path) -> dict:
    """Compile one already-matched source and byte-gate it. Returns a result record."""
    report_path = report_dir / f"{entry['module']}_{entry['addr']}.json"
    report_path.unlink(missing_ok=True)
    argv = [sys.executable, str(BYTEGATE), entry["module"], entry["addr"],
            "--src-root", str(src_root), "--ledger", str(ledger),
            "--toolchain", str(toolchain), "--build-config", str(build_config),
            "--nso", str(nso), "--build-dir", str(build_dir),
            "--ref-bin", str(ref_bin), "--report", str(report_path), "--no-color"]
    if body is not None:
        argv += ["--body", str(body)]
    proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, check=False)
    report = json.loads(report_path.read_text()) if report_path.exists() else None
    return result_from_report(entry, report, proc.returncode,
                              proc.stdout + proc.stderr)


def body_for(entry: dict, sizes: dict[str, int], text: bytes | None,
             warnings: list[str]) -> int | None:
    """The validated instruction-plus-pool extent, or ``None`` to fail closed.

    Missing inventory/reference data and invalid pool targets are reported as warnings;
    the gate then returns ``missing-body`` rather than comparing a candidate-sized prefix.
    """
    try:
        body, _ = resolve_body(entry, sizes)
    except BundleError:
        warnings.append(f"{entry['name']}: not in inventory; no gate extent")
        return None
    raw = complexity.body_of(text, entry["addr"], body) if text is not None else None
    try:
        return complexity.function_extent(raw, int(entry["size"]))
    except ValueError as e:
        warnings.append(f"{entry['name']}: {e}; no gate extent")
        return None


def run(entries: list[dict], *, toolchain: Path, clang: str, src_root: Path,
        ledger: Path, nso: Path, build_config: Path, inventory: Path, work: Path,
        jobs: int = 1) -> list[dict]:
    """Re-gate ``entries``; returns results in input order regardless of job count."""
    text = complexity.load_text(nso)
    if text is None:
        raise SetupError(f"cannot read reference .text from {nso} "
                         f"(needed to slice bodies and write --ref-bin)")
    ref_bin = write_ref_bin(text, work)
    sizes = (parse_inventory(inventory.read_text()) if inventory.exists() else {})
    warnings: list[str] = []

    build_dir = work / "obj"
    report_dir = work / "reports"
    build_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    prepared = []
    for entry in entries:
        body = body_for(entry, sizes, text, warnings)
        prepared.append((entry, body))

    def one(item):
        entry, body = item
        return gate_one(entry, toolchain=toolchain, src_root=src_root, ledger=ledger,
                        nso=nso, build_config=build_config, ref_bin=ref_bin, body=body,
                        build_dir=build_dir, report_dir=report_dir)

    if jobs <= 1 or len(prepared) <= 1:
        results = [one(item) for item in prepared]
    else:
        # Warm the shared GOT/PLT stub cache before fanning out so parallel gate
        # runs never race to build it.
        first = one(prepared[0])
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            rest = list(pool.map(one, prepared[1:]))
        results = [first, *rest]

    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    return results


def write_tsv(path: Path, results: list[dict]) -> None:
    """One unexplained regression per line; matches and accepted residuals are omitted."""
    lines = ["addr\tname\tstatus\tdiff_count\trc"]
    for r in results:
        if r.get("ok") or r.get("classification") == "known-residual":
            continue
        lines.append(f"{r['addr']}\t{r['name']}\t{r.get('status') or 'error'}\t"
                     f"{'' if r.get('diff_count') is None else r['diff_count']}\t{r.get('rc')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--src-root", type=Path, default=DEFAULT_SRC_ROOT)
    ap.add_argument("--toolchain", type=Path, default=DEFAULT_TOOLCHAIN,
                    help="candidate compiler profile (default: the 4.0.1 profile)")
    ap.add_argument("--clang", default=None,
                    help="override the profile's compiler binary (e.g. an extracted "
                         "tarball before the devcontainer is rebuilt)")
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO)
    ap.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    ap.add_argument("--build-config", type=Path, default=DEFAULT_BUILD_CONFIG)
    ap.add_argument("--module", default=None, help="restrict to one module")
    ap.add_argument("--limit", type=int, default=0, help="max entries (0 = all)")
    ap.add_argument("--jobs", type=int, default=1, help="parallel gate runs (default 1)")
    ap.add_argument("--work", type=Path, default=DEFAULT_WORK)
    ap.add_argument("--report", type=Path, default=None,
                    help="write the machine-readable summary here (JSON)")
    ap.add_argument("--tsv", type=Path, default=None,
                    help="write one regression per line as TSV here")
    ap.add_argument("--known-residuals", default=str(DEFAULT_KNOWN_RESIDUALS),
                    metavar="FILE",
                    help="reviewed compiler-residual baseline (default); pass an empty "
                         "string to require every selected function to match")
    ap.add_argument("--show-diffs", type=int, default=10, metavar="N",
                    help="print the first N regressions with their differing words")
    args = ap.parse_args(argv)

    baseline = None
    baseline_path = Path(args.known_residuals) if args.known_residuals else None
    if baseline_path is not None:
        try:
            baseline = read_known_residuals(baseline_path)
        except (OSError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2

    if not args.ledger.exists():
        print(f"error: missing ledger {args.ledger}", file=sys.stderr)
        return 2
    if not args.nso.exists():
        print(f"error: missing NSO {args.nso}", file=sys.stderr)
        return 2
    if args.limit < 0 or args.jobs < 1:
        ap.error("--limit must be >= 0 and --jobs >= 1")

    entries = selected(read_entries(args.ledger), module=args.module, limit=args.limit)
    if not entries:
        print("error: no matched functions selected", file=sys.stderr)
        return 2
    if baseline is not None:
        # A module/limit subset is judged only against the residuals in that subset;
        # baseline entries outside it are not "missing".
        selected_keys = {(e["module"], e["addr"]) for e in entries}
        baseline = {k: v for k, v in baseline.items() if k in selected_keys}

    args.work.mkdir(parents=True, exist_ok=True)
    try:
        profile, data = effective_profile(args.toolchain, args.clang, args.work)
        clang = resolve_clang(data)
    except SetupError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    version = clang_version(clang)

    print(f"revalidate: {len(entries)} matched function(s)")
    print(f"  profile: {args.toolchain}")
    print(f"  clang:   {clang}  ({version})")
    print(f"  work:    {args.work}")
    print()

    try:
        results = run(entries, toolchain=profile, clang=clang, src_root=args.src_root,
                      ledger=args.ledger, nso=args.nso, build_config=args.build_config,
                      inventory=args.inventory, work=args.work, jobs=args.jobs)
    except SetupError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if baseline is not None:
        classified = classify_residuals(results, baseline)
        summary_results = classified["results"]
        regs = classified["regressions"]
        resolved = classified["resolved_residuals"]
        missing = classified["missing_residuals"]
    else:
        summary_results = results
        regs = regressions(results)
        resolved = []
        missing = []

    counts = summarize(summary_results)
    print(f"result: {format_counts(counts)}")
    if baseline is not None:
        known_count = counts.get("known-residual", 0)
        print(f"known residuals: {known_count} accepted; "
              f"resolved={len(resolved)} missing={len(missing)}")
    print(f"regressions: {len(regs)}/{len(results)}")

    shown = regs[:max(0, args.show_diffs)]
    for r in shown:
        print(f"  {r['addr']}  {r['name']:<24} {r['status']:<14} "
              f"diffs={r['diff_count'] if r['diff_count'] is not None else '-'}")
        for w in r["diff_words"][:4]:
            print(f"      +0x{w['offset']:x}  got {w['got']}  want {w['want']}")
        if r.get("detail") and r["status"] == "error":
            print(f"      {r['detail'].splitlines()[-1] if r['detail'].splitlines() else ''}")
    if len(regs) > len(shown):
        print(f"  ... {len(regs) - len(shown)} more (raise --show-diffs or use --tsv)")

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(
            build_report(str(args.toolchain), clang, version, results,
                         baseline=baseline),
            indent=2, sort_keys=True) + "\n")
        print(f"report: {args.report}")
    if args.tsv is not None:
        write_tsv(args.tsv, summary_results)
        print(f"tsv:    {args.tsv}")

    return 1 if regs or resolved or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
