"""The reconstruction driver: one loop iteration per ledger entry.

It is glue, not a new capability — it wires the already-built, independently-testable parts
into the loop from ``docs/llm-harness-design.md`` → *The harness*::

    select -> bundle -> model -> write -> gate -> bank / record

Per entry it selects the next pending ``function`` (``worklist``), builds the annotated
context (``bundle``), asks the configured endpoint (``model``), writes the candidate to its
ledger-derived source path, and hands it to the **independent** byte gate
(``tools/ledger/bytegate.py``). The gate decides; the driver never claims a match itself.

Two rules shape the code, both from the design doc:

* **The gate is the only writer of ``verify``.** The driver always invokes the gate with
  ``--update``; the gate writes ``verify=match`` *only* on a real match, so the driver never
  edits that axis.
* **Containment is by construction.** The model only ever returns text. Every path the
  driver writes is derived **solely from the ledger** (``src/<module>/<group>.cpp`` and
  ``baserom/work/attempts/…``), guarded by a resolve-and-require-under-root check; model text
  is written to a file and never enters argv, a shell, ``eval``, or a compiler flag. Compilation
  is a fixed-argv, in-container subprocess.

On a **match** the candidate stays in ``src/`` and the gate has banked it. On a **near miss**
the draft is moved out of ``src/`` so it holds matched code only — never discarded
(``AGENTS.md``): every attempt is appended to the parent-linked log (``attempts.py``), and the
strictly-improving near-miss bank (``nearmiss.py``, under the eval pin) keeps the closest so far.

Usage::

    python3 tools/loop/run.py                         # one entry (next pending, easiest first)
    python3 tools/loop/run.py --limit 5               # five entries
    python3 tools/loop/run.py --order addr            # select in the ledger's own order
    python3 tools/loop/run.py --entry 601a72e4        # a specific entry
    python3 tools/loop/run.py --entry 601a72e4 --attempts 5   # resample until it matches
    python3 tools/loop/run.py --dry-run                # select + bundle + prompt, no model
    python3 tools/loop/run.py --rebuild                # regenerate the bundle (Ghidra)
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))
sys.path.insert(0, str(REPO / "tools" / "loop"))

import attempts
import bundle
import complexity
import model as model_client
import nearmiss
import worklist
from ledgerlib import entry_key, read_entries

BYTEGATE = REPO / "tools" / "ledger" / "bytegate.py"
BUNDLE = REPO / "tools" / "loop" / "bundle.py"

SYSTEM = (
    "You reconstruct C/C++ functions from ARM (AArch32) disassembly for a byte-matching "
    "decompilation. Reply with a complete translation unit (the function definition and any "
    "declarations it needs). Never use inline assembly (__asm__) or top-level asm statements — "
    "the compiler must generate the instructions from ordinary C/C++. No prose, no Markdown "
    "fences.")


@dataclass
class Layout:
    """The fixed paths one run reads from and writes to (all repo-relative)."""

    ledger: Path = REPO / "config" / "main" / "ledger.tsv"
    inventory: Path = bundle.DEFAULT_INVENTORY
    nso: Path = bundle.DEFAULT_NSO
    context: Path = REPO / "baserom" / "work" / "context"
    src_root: Path = REPO / "src"
    build_config: Path = REPO / "config" / "build.json"
    toolchain: Path = REPO / "config" / "toolchain.json"
    work: Path = REPO / "baserom" / "work"
    model_config: Path = REPO / "config" / "model.json"


# --- pure helpers (unit-tested) -------------------------------------------------------

def safe_draft_path(entry: dict, src_root: Path) -> Path:
    """The one source path a candidate for ``entry`` may be written to.

    Derived **solely from the ledger**; a module or group containing a path separator or
    ``..`` is refused outright, so ledger data can never escape the source root.
    """
    module, group = entry["module"], entry["group"]
    for part in (module, group):
        if not part or "/" in part or "\\" in part or part in (".", ".."):
            raise ValueError(f"unsafe ledger path component: {part!r}")
    return Path(src_root) / module / f"{group}.cpp"


def ensure_under(path: Path, root: Path) -> Path:
    """Resolve ``path`` and require it to live under ``root``; return the resolved path."""
    resolved, resolved_root = Path(path).resolve(), Path(root).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"refusing to write outside {resolved_root}: {resolved}")
    return resolved


def context_path(layout: Layout, entry: dict) -> Path:
    return layout.context / entry["module"] / f"{entry['addr']}.md"


def attempt_store(layout: Layout) -> Path:
    return layout.work / "attempts"


def bank_path(layout: Layout) -> Path:
    return layout.work / "nearmiss" / "bank.json"


def group_is_single(entries: list[dict], module: str, group: str) -> bool:
    """Whether exactly one ``function`` entry uses this ``(module, group)`` translation unit.

    A draft may only be removed from ``src/`` when the file is *this* entry's alone; a merged
    translation unit (several entries sharing a group) must be left untouched.
    """
    return sum(1 for e in entries
               if e["module"] == module and e["group"] == group
               and e["kind"] == "function") == 1


def build_prompt(entry: dict, bundle_text: str) -> str:
    """The user prompt: the required symbol plus the whole context bundle.

    The instructions are load-bearing: an early pilot had the model reproduce the disassembly
    as inline ``__asm__`` (which cannot match the surrounding codegen and, as written, did not
    even compile). Plain C/C++ is required; an ``asm`` label is only for a symbol that is not a
    valid identifier. A later pilot modelled a run of words as two *anonymous* structs, which is
    ill-formed (they are distinct types); the instructions now require a named type.
    """
    name = entry["name"]
    if name.isidentifier():
        symbol = f'Define it with `extern "C"` so the object symbol is exactly `{name}`.'
    else:
        symbol = (f"`{name}` is not a valid C++ identifier; give the function a C++-legal name "
                  f'and bind it to the exact symbol with a trailing asm("{name}") on its '
                  f"declaration.")
    return (
        f"Write ordinary C or C++ whose compiled machine code reproduces the function below "
        f"exactly under the pinned toolchain. Reason about the function's *behaviour*, not its "
        f"registers: the register allocation was the original compiler's choice and yours will "
        f"differ. Do NOT use inline assembly (__asm__) or a top-level asm() statement. The ARM "
        f"AAPCS ABI applies: r0-r3 carry the arguments and r0 the result; the prologue and "
        f"epilogue are generated for you.\n\n"
        f"A run of words moved by `ldmia`/`stmia` is ONE by-value struct copy, not per-word "
        f"moves. Consecutive load/store-multiple blocks that walk contiguous addresses move a "
        f"single object: add the words up (registers x blocks) to get its size, and give it a "
        f"*named* type (two separately-written anonymous struct types are distinct and will not "
        f"assign). Model the destination offset as a struct field and copy with one assignment.\n\n"
        f"Take each struct's layout from the instructions that touch it. A field's offset is the "
        f"displacement in its load/store — `ldrb r3, [r0, #0x20]` puts that field at +0x20. An "
        f"array element's size is the pointer-increment constant — `add r0, r0, #0x30` means "
        f"sizeof(element) is exactly 0x30; pad the struct so its size equals that constant. Fields "
        f"need not be adjacent — place each at its exact displacement and insert explicit padding "
        f"for the gaps; do not assume one field immediately follows another. Do not guess any of "
        f"these values. For example, if a field loads at `[r0, #0x58]` and the previous field is "
        f"a 4-byte value at `[r0, #0x40]`, the second field's offset is 0x58 (not 0x44), so pad "
        f"0x58 - 0x44 = 0x14 bytes: the displacement is the offset, and the padding is whatever "
        f"makes the field land exactly there.\n\n"
        f"Worked example (a different function — it shows the idiom, not this answer):\n"
        f"    ldmia r1!, {{r2,r3,r12,lr}}    ; 4 words from src, src += 16\n"
        f"    add   r0, r0, #0x10\n"
        f"    stmia r0!, {{r2,r3,r12,lr}}    ; 4 words to dst+0x10, dst += 16\n"
        f"    ldmia r1, {{r2,r3,r12,lr}}     ; 4 words from src+16\n"
        f"    stmia r0, {{r2,r3,r12,lr}}     ; 4 words to dst+0x20\n"
        f"  is one 32-byte struct at offset 0x10 (4 + 4 = 8 words), copied by value:\n"
        f"    struct Blob   {{ unsigned int w[8]; }};\n"
        f"    struct Holder {{ char pad[0x10]; Blob b; }};\n"
        f'    extern "C" void f(Holder *h, const Blob *src) {{ h->b = *src; }}\n'
        f"{symbol}\n"
        f"Reply with the translation unit only — no prose, no Markdown fences.\n\n"
        f"{bundle_text}\n"
    )


def bundle_argv(layout: Layout, entry: dict, body: int) -> list[str]:
    return [sys.executable, str(BUNDLE), entry["module"], entry["addr"],
            "--ledger", str(layout.ledger), "--inventory", str(layout.inventory),
            "--nso", str(layout.nso), "--out", str(layout.context),
            "--body", str(body)]


def gate_argv(layout: Layout, entry: dict, body: int,
              report: Path | None = None) -> list[str]:
    """The byte-gate invocation. Fixed argv: no model text ever reaches it."""
    argv = [sys.executable, str(BYTEGATE), entry["module"], entry["addr"],
            "--src-root", str(layout.src_root), "--ledger", str(layout.ledger),
            "--toolchain", str(layout.toolchain), "--build-config", str(layout.build_config),
            "--nso", str(layout.nso), "--body", str(body), "--update"]
    if report is not None:
        argv += ["--report", str(report)]
    return argv


def select_next(entries: list[dict], layout: Layout, *, skip_existing: bool,
                done: set[tuple[str, str]],
                key=None) -> dict | None:
    """The next pending function not already handled this run.

    ``key`` is the optional difficulty ordering (``complexity.make_key``); ``None`` keeps the
    ledger's own ``(module, addr)`` order. Both stay deterministic, so a resume is unaffected.
    """
    queue = worklist.select(entries, kind="function", verify="none", key=key)
    if skip_existing:
        queue = [e for e in queue if not worklist.source_path(e, layout.src_root).exists()]
    for entry in queue:
        if entry_key(entry) not in done:
            return entry
    return None


def complexity_key(layout: Layout):
    """The easy-first selector key, or ``None`` to fall back to address order.

    The reference ``.text`` comes from the NSO in pure Python (no Ghidra); if it is
    unavailable the ordering degrades to the ledger's own order rather than failing the run.
    """
    text = complexity.load_text(layout.nso)
    if text is None:
        print("warning: reference .text unavailable for --order easiest; using address order",
              file=sys.stderr)
        return None
    sizes = (bundle.parse_inventory(layout.inventory.read_text())
             if layout.inventory.exists() else {})
    blocks = complexity.load_blocks(layout.inventory.with_name("inventory.blocks.tsv"))
    return complexity.make_key(text, sizes, blocks)


def resolve_entry(entries: list[dict], module: str, addr: str) -> dict:
    """Find the ``--entry`` target; ``addr`` is normalized, ``module`` defaults to main."""
    return bundle.find_entry(entries, module, addr.lower().removeprefix("0x").zfill(8))


# --- impure steps ---------------------------------------------------------------------

def run_subprocess(argv: list[str]) -> tuple[int, str]:
    result = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout + result.stderr


def resolve_body(layout: Layout, entry: dict, override: int | None) -> tuple[int, str]:
    sizes = (bundle.parse_inventory(layout.inventory.read_text())
             if layout.inventory.exists() else {})
    return bundle.resolve_body(entry, sizes, override)


def prompt_fingerprint(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=Layout.ledger)
    ap.add_argument("--inventory", type=Path, default=Layout.inventory)
    ap.add_argument("--nso", type=Path, default=Layout.nso)
    ap.add_argument("--context", type=Path, default=Layout.context)
    ap.add_argument("--src-root", type=Path, default=Layout.src_root)
    ap.add_argument("--work", type=Path, default=Layout.work)
    ap.add_argument("--model-config", type=Path, default=Layout.model_config)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--endpoint", default=None)
    ap.add_argument("--model-name", default=None)
    ap.add_argument("--proxy", default=None)
    ap.add_argument("--timeout", type=float, default=None,
                    help="model request timeout in seconds (a cold load can be slow)")
    ap.add_argument("--temperature", type=float, default=None,
                    help="sampling temperature override (omit to use the server/preset default)")
    ap.add_argument("--seed", type=int, default=None, help="sampling seed override (optional)")
    ap.add_argument("--body", type=int, default=None)
    ap.add_argument("--module", default="main", help="module for --entry (default: main)")
    ap.add_argument("--entry", default=None, help="target one ledger address (in --module)")
    ap.add_argument("--limit", type=int, default=1, help="entries to process (default 1)")
    ap.add_argument("--order", choices=("easiest", "addr"), default="easiest",
                    help="auto-select order when no --entry: 'easiest' (difficulty, default) "
                         "or 'addr' (the ledger's own order)")
    ap.add_argument("--attempts", type=int, default=1,
                    help="attempts per entry, stopping early on a match (default 1)")
    ap.add_argument("--force", action="store_true",
                    help="process entries whose source already exists (overwrites)")
    ap.add_argument("--no-skip-existing", dest="skip_existing", action="store_false",
                    help="do not skip entries whose source exists (implies --force risk)")
    ap.add_argument("--rebuild", action="store_true", help="regenerate the bundle (Ghidra)")
    ap.add_argument("--dry-run", action="store_true",
                    help="select, bundle and print the prompt; do not call the model")
    args = ap.parse_args(argv)

    layout = Layout(ledger=args.ledger, inventory=args.inventory, nso=args.nso,
                    context=args.context, src_root=args.src_root, work=args.work,
                    model_config=args.model_config)

    if not layout.ledger.exists():
        print(f"error: missing ledger {layout.ledger}", file=sys.stderr)
        return 2
    entries = read_entries(layout.ledger)

    # One explicit target, or the next N pending entries.
    targets: list[dict] = []
    done: set[tuple[str, str]] = set()
    if args.entry:
        try:
            targets = [resolve_entry(entries, args.module, args.entry)]
        except bundle.BundleError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    else:
        key = complexity_key(layout) if args.order == "easiest" else None
        for _ in range(max(1, args.limit)):
            nxt = select_next(entries, layout, skip_existing=args.skip_existing, done=done,
                              key=key)
            if nxt is None:
                break
            done.add(entry_key(nxt))
            targets.append(nxt)
    if not targets:
        print("error: no pending entries to process", file=sys.stderr)
        return 1

    model = None
    if not args.dry_run:
        try:
            model = model_client.from_config(
                layout.model_config, override_base_url=args.base_url,
                override_model=args.model_name, override_endpoint=args.endpoint,
                override_proxy=args.proxy, override_timeout=args.timeout,
                override_temperature=args.temperature, override_seed=args.seed)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"error: bad model config: {e}", file=sys.stderr)
            return 2

    matched = 0
    attempts_run = 0
    try:
        for entry in targets:
            outcome, used = attempt_entry(entry, entries, layout, args, model)
            attempts_run += used
            matched += outcome == "match"
    except KeyboardInterrupt:
        print(f"\ninterrupted: {attempts_run} attempt(s), {matched} match(es)",
              file=sys.stderr)
        return 130

    if args.dry_run:
        print(f"dry-run: {len(targets)} entry(ies) previewed")
        return 0
    print(f"done: {attempts_run} attempt(s), {matched} match(es)")
    return 0


@contextlib.contextmanager
def heartbeat(label: str, interval_s: float = 15.0):
    """Print a periodic "still running" line on stderr while a blocking call is in flight.

    A model call can take minutes (a cold load, or a long reasoning trace), so a silent wait is
    indistinguishable from a hang. A daemon thread prints an elapsed-time line every
    ``interval_s`` and is stopped when the block exits, including on an exception.
    """
    stop = threading.Event()

    def beat() -> None:
        waited = 0.0
        while not stop.wait(interval_s):
            waited += interval_s
            print(f"    \u2026 {label} still running ({waited:.0f}s)",
                  file=sys.stderr, flush=True)

    thread = threading.Thread(target=beat, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join()


def process(entry: dict, entries: list[dict], layout: Layout, args, model) -> str:
    """One loop iteration. Returns 'match' | 'mismatch' | 'error'."""
    module, addr, name = entry["module"], entry["addr"], entry["name"]

    body, extent_source = resolve_body(layout, entry, args.body)

    # 1. context bundle (reuse unless --rebuild).
    md = context_path(layout, entry)
    if args.rebuild or not md.exists():
        rc, out = run_subprocess(bundle_argv(layout, entry, body))
        if rc != 0:
            raise bundle.BundleError(f"bundle failed:\n{out.strip()[-800:]}")
    bundle_text = md.read_text()

    # 2. prompt.
    prompt = build_prompt(entry, bundle_text)

    if args.dry_run:
        print(f"--- prompt for {name} ({body} B, {extent_source}) ---")
        print(prompt)
        return "dry-run"

    # 3. model.
    print(f"    asking {getattr(model, 'model', 'model')} …", file=sys.stderr, flush=True)
    with heartbeat(name):
        completion = model.complete(prompt, system=SYSTEM)
    print(f"    reply in {completion.latency_s:.0f}s ({completion.completion_tokens} tok)",
          file=sys.stderr, flush=True)
    candidate = model_client.strip_fences(completion.text)
    if not candidate.strip():
        print(f"{name}: empty candidate from the model")
        return "error"

    # 4. write the candidate to its ledger-derived source path (containment guard).
    draft = ensure_under(safe_draft_path(entry, layout.src_root), layout.src_root)
    if draft.exists() and not args.force:
        raise ValueError(f"{draft} exists (use --force to overwrite)")
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(candidate)

    # 5. verify — the gate decides and (only on a match) banks verify=match.
    report_path = layout.work / "bytegate" / f"{module}_{addr}.report.json"
    report_path.unlink(missing_ok=True)
    rc, gate_out = run_subprocess(gate_argv(layout, entry, body, report_path))
    report = json.loads(report_path.read_text()) if report_path.exists() else None
    # The report's presence is the source of truth: the gate writes it only after a successful
    # compare. No report means the candidate did not compile (rc 3) or the gate errored.
    if report is not None:
        outcome = "match" if report["ok"] else "mismatch"
    else:
        outcome = "error"

    # 6. record the attempt (append-only, parent-linked) — every attempt is kept.
    record = {
        "module": module, "addr": addr, "name": name, "body": body,
        "extent_source": extent_source, "outcome": outcome, "gate_rc": rc,
        "model": completion.model, "prompt_tokens": completion.prompt_tokens,
        "completion_tokens": completion.completion_tokens, "latency_s": completion.latency_s,
        "prompt_sha256": prompt_fingerprint(prompt), "gate_output": gate_out.strip()[-4000:],
    }
    if report is not None:
        record["gate_status"] = report["status"]
        record["diff_count"] = report["diff_count"]
    stored = attempts.append(attempt_store(layout), record, candidate_text=candidate)

    # 7. bank a near miss (strictly-improving), and keep src/ matched-only.
    if outcome == "match":
        print(f">>> MATCH  {name}  -> {draft}  (attempt {stored['id']})")
    else:
        if report is not None:
            dist = nearmiss.closeness(report["diff_count"], report["cand_len"], body)
            pin = nearmiss.eval_pin(layout.toolchain)
            result = nearmiss.record(bank_path(layout), module, addr, dist, pin,
                                     name=name, attempt_id=stored["id"],
                                     gate_status=report["status"])
            if result.get("warn"):
                print(f"  warning: {result['warn']}", file=sys.stderr)
            note = (f"closeness={dist} ({result['reason']})" if result["updated"]
                    else f"closeness={dist} (kept {result['previous']})")
        else:
            note = f"no gate report (rc={rc})"
        if group_is_single(entries, module, entry["group"]):
            draft.unlink(missing_ok=True)
        else:
            print(f"  note: {entry['group']} is a merged TU; leaving {draft} in place")
        print(f"    {outcome.upper()}  {name}  attempt {stored['id']}  {note}")
    return outcome


def attempt_entry(entry: dict, entries: list[dict], layout: Layout, args, model,
                  one=process) -> tuple[str, int]:
    """Run one entry up to ``args.attempts`` times, stopping on a match.

    Returns ``(outcome, attempts_used)``. Every attempt is recorded (parent-linked) by
    ``process``; a transport or bundle error counts as an attempt and is retried, since a
    runaway generation or a cold-load timeout is often transient. ``--dry-run`` previews once.
    """
    outcome = "error"
    used = 0
    for _ in range(max(1, args.attempts)):
        try:
            outcome = one(entry, entries, layout, args, model)
        except (attempts.AttemptError, bundle.BundleError, model_client.ModelError,
                ValueError) as e:
            print(f"error: {entry['name']}: {e}", file=sys.stderr)
            outcome = "error"
        used += 1
        if outcome in ("match", "dry-run"):
            break
    return outcome, used


if __name__ == "__main__":
    raise SystemExit(main())
