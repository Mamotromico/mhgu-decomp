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
    python3 tools/loop/run.py --entry 601a72e4 --attempts 5 --no-feedback  # plain resampling
    python3 tools/loop/run.py --dry-run                # select + bundle + prompt, no model
    python3 tools/loop/run.py --rebuild                # regenerate the bundle (Ghidra)
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))
sys.path.insert(0, str(REPO / "tools" / "loop"))

import attempts
import bundle
import complexity
import model as model_client
import nearmiss
import templates
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

# A rendered bundle disassembly line: `    <addr>  <bytes>  <mnemonic> <operands> [; notes]`.
_BUNDLE_INSN = re.compile(r"^\s+([0-9a-f]{8})\s+([0-9a-f]+)\s+(\S+)\s*(.*)$")

# The by-value struct-copy guidance is only worth its weight when a block move is actually
# present, so it is included conditionally (see ``has_nonstack_block_move``).
_STRUCT_COPY_SECTION = (
    "A run of words moved by `ldmia`/`stmia` is ONE by-value struct copy, not per-word "
    "moves. Consecutive load/store-multiple blocks that walk contiguous addresses move a "
    "single object: add the words up (registers x blocks) to get its size, and give it a "
    "*named* type (two separately-written anonymous struct types are distinct and will not "
    "assign). Model the destination offset as a struct field and copy with one assignment.\n\n"
    "Worked example (a different function — it shows the idiom, not this answer):\n"
    "    ldmia r1!, {r2,r3,r12,lr}    ; 4 words from src, src += 16\n"
    "    add   r0, r0, #0x10\n"
    "    stmia r0!, {r2,r3,r12,lr}    ; 4 words to dst+0x10, dst += 16\n"
    "    ldmia r1, {r2,r3,r12,lr}     ; 4 words from src+16\n"
    "    stmia r0, {r2,r3,r12,lr}     ; 4 words to dst+0x20\n"
    "  is one 32-byte struct at offset 0x10 (4 + 4 = 8 words), copied by value:\n"
    "    struct Blob   { unsigned int w[8]; };\n"
    "    struct Holder { char pad[0x10]; Blob b; };\n"
    '    extern "C" void f(Holder *h, const Blob *src) { h->b = *src; }\n\n')


def has_nonstack_block_move(bundle_text: str) -> bool:
    """Whether the bundle disassembly has an ``ldm``/``stm`` whose base is not the stack.

    The by-value struct-copy section only pays off when such a block move is present; the
    ``push``/``pop`` save every non-leaf function has is sp-based (or printed as ``push``/``pop``)
    and must not trigger it. This keeps the prompt's strongest worked example aligned with the
    idiom's ~1% incidence (see ``docs/llm-harness-design.md`` → *Template growth is measured*).
    """
    for line in bundle_text.splitlines():
        m = _BUNDLE_INSN.match(line)
        if not m:
            continue
        mnemonic, operands = m.group(3), m.group(4)
        if mnemonic.startswith(("ldm", "stm")) and "sp" not in operands:
            return True
    return False


@dataclass
class Feedback:
    """The previous attempt's outcome, fed into the next prompt (a retry only).

    Built from the attempt log (:func:`feedback_from_record`), so it reflects what the gate
    actually said, never a re-derivation. ``candidate`` is the previous translation unit (for
    the model to edit); ``diff_words``/``compile_error`` are the actionable divergence.
    """

    outcome: str
    status: str | None = None
    diff_count: int | None = None
    diff_words: list = field(default_factory=list)
    candidate: str | None = None
    compile_error: str | None = None


def parse_reference_instructions(bundle_text: str, base_addr: str) -> dict[int, str]:
    """Map body-relative offset -> original instruction text, from the bundle's disassembly.

    The bundle lists absolute addresses; ``base_addr`` is the entry address, so the offset of a
    line is ``addr - base_addr`` — the same frame the gate's ``diff_words`` offsets use. Only the
    ``## disassembly`` section is read (the later ``## calls`` section is ignored).
    """
    base = int(base_addr, 16)
    out: dict[int, str] = {}
    inside = False
    for line in bundle_text.splitlines():
        if line.startswith("## "):
            inside = line.startswith("## disassembly")
            continue
        if not inside:
            continue
        m = _BUNDLE_INSN.match(line)
        if m:
            out[int(m.group(1), 16) - base] = f"{m.group(3)} {m.group(4)}".strip()
    return out


def feedback_section(entry: dict, bundle_text: str,
                     feedback: "Feedback | None") -> str:
    """Render the retry guidance appended to the prompt; empty when there is no feedback.

    A mismatch names the exact instructions that differ (offset, candidate bytes, reference
    bytes, and the reference mnemonic when the bundle carries it); a compile error quotes the
    compiler. The previous translation unit is included so the model edits rather than regenerates.
    """
    if feedback is None:
        return ""
    if feedback.compile_error:
        body = (
            "## Previous attempt did not compile\n\n"
            "The compiler rejected the last translation unit:\n\n"
            "```\n" + feedback.compile_error.strip()[-1200:] + "\n```\n\n"
            "Return a corrected translation unit that compiles.")
    else:
        ref = parse_reference_instructions(bundle_text, entry["addr"])
        rows = []
        for w in feedback.diff_words:
            insn = ref.get(w["offset"])
            rows.append(f"    +0x{w['offset']:x}  got {w['got']}  want {w['want']}"
                        + (f"   ; original: {insn}" if insn else ""))
        if not rows:
            rows.append(f"    (compiled body {feedback.status}; see the disassembly above)")
        body = (
            "## Previous attempt did not match\n\n"
            "The last candidate compiled, but the machine code differs from the original "
            f"({feedback.diff_count} differing byte(s)). Fix ONLY the instructions below; keep "
            "the rest of the translation unit unchanged. `got` is your bytes, `want` is the "
            "original's; registers may differ by design, so prefer a source change that makes "
            "the compiler emit the `want` instruction:\n\n"
            + "\n".join(rows))
    parts = [body]
    if feedback.candidate:
        parts.append("--- your previous translation unit ---\n"
                     + feedback.candidate.strip() + "\n--- end ---")
    return "\n\n".join(parts) + "\n"


def feedback_from_record(record: dict | None, store_dir: Path) -> Feedback | None:
    """The retry feedback for a recorded attempt, or ``None`` if it is not actionable.

    Only a ``mismatch`` or ``error`` carries feedback (a ``match`` needs no retry). The previous
    candidate blob, if present, is read back so the model can revise it.
    """
    if not record or record.get("outcome") not in ("mismatch", "error"):
        return None
    candidate = None
    rel = record.get("candidate")
    if rel:
        blob = Path(store_dir) / rel
        if blob.exists():
            candidate = blob.read_text()
    if record["outcome"] == "error":
        return Feedback("error", candidate=candidate,
                        compile_error=record.get("gate_output") or "")
    return Feedback("mismatch", status=record.get("gate_status"),
                    diff_count=record.get("diff_count"),
                    diff_words=record.get("diff_words") or [], candidate=candidate)


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


def build_prompt(entry: dict, bundle_text: str, feedback: "Feedback | None" = None) -> str:
    """The user prompt: the required symbol plus the whole context bundle.

    The instructions are load-bearing: an early pilot had the model reproduce the disassembly
    as inline ``__asm__`` (which cannot match the surrounding codegen and, as written, did not
    even compile). Plain C/C++ is required; an ``asm`` label is only for a symbol that is not a
    valid identifier. A later pilot modelled a run of words as two *anonymous* structs, which is
    ill-formed (they are distinct types); the instructions now require a named type. The
    struct-copy guidance is now **conditional** (``has_nonstack_block_move``): it is included
    only when the bundle actually carries a non-stack ``ldm``/``stm``, so a rare idiom no longer
    dominates the prompt (see ``docs/llm-harness-design.md`` → *Template growth is measured*).

    ``feedback`` (a retry only, so ``None`` on the first attempt) appends the previous attempt's
    divergence — the exact instructions that differ, or the compiler error — so a retry improves
    on the previous try instead of resampling the identical prompt. With ``feedback is None`` the
    output is byte-identical to the pre-feedback prompt.
    """
    name = entry["name"]
    if name.isidentifier():
        symbol = f'Define it with `extern "C"` so the object symbol is exactly `{name}`.'
    else:
        symbol = (f"`{name}` is not a valid C++ identifier; give the function a C++-legal name "
                  f'and bind it to the exact symbol with a trailing asm("{name}") on its '
                  f"declaration.")
    copy_section = _STRUCT_COPY_SECTION if has_nonstack_block_move(bundle_text) else ""
    return (
        f"Write ordinary C or C++ whose compiled machine code reproduces the function below "
        f"exactly under the pinned toolchain. Reason about the function's *behaviour*, not its "
        f"registers: the register allocation was the original compiler's choice and yours will "
        f"differ. Do NOT use inline assembly (__asm__) or a top-level asm() statement. The ARM "
        f"AAPCS ABI applies: r0-r3 carry the arguments and r0 the result; the prologue and "
        f"epilogue are generated for you.\n\n"
        f"{copy_section}"
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
        f"{symbol}\n"
        f"Reply with the translation unit only — no prose, no Markdown fences.\n\n"
        f"{bundle_text}\n"
        f"{feedback_section(entry, bundle_text, feedback)}"
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


def complexity_key(layout: Layout, text: bytes | None):
    """The easy-first selector key from a reference ``.text``, or ``None`` for address order."""
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
    ap.add_argument("--no-feedback", dest="feedback", action="store_false",
                    help="on a retry, do not feed the previous attempt's divergence back into "
                         "the prompt (resample the base prompt; also disables the stall stop)")
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
    # One reference ``.text`` read serves both the easy-first ordering and the template pass.
    reference = complexity.load_text(layout.nso)

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
        key = complexity_key(layout, reference) if args.order == "easiest" else None
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
            outcome, used = attempt_entry(entry, entries, layout, args, model,
                                          raw_text=reference)
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


def build_bundle_text(layout: Layout, entry: dict, args, body: int) -> str:
    """The context bundle for ``entry`` (reused unless ``--rebuild``; one Ghidra import)."""
    md = context_path(layout, entry)
    if args.rebuild or not md.exists():
        rc, out = run_subprocess(bundle_argv(layout, entry, body))
        if rc != 0:
            raise bundle.BundleError(f"bundle failed:\n{out.strip()[-800:]}")
    return md.read_text()


def ask_model(entry: dict, layout: Layout, args, model, body: int,
              feedback: "Feedback | None" = None):
    """Bundle, prompt, and call the model. Returns ``(candidate, completion, prompt)``."""
    prompt = build_prompt(entry, build_bundle_text(layout, entry, args, body), feedback)
    print(f"    asking {getattr(model, 'model', 'model')} …", file=sys.stderr, flush=True)
    with heartbeat(entry["name"]):
        completion = model.complete(prompt, system=SYSTEM)
    print(f"    reply in {completion.latency_s:.0f}s ({completion.completion_tokens} tok)",
          file=sys.stderr, flush=True)
    return model_client.strip_fences(completion.text), completion, prompt


def write_and_gate(entry: dict, layout: Layout, body: int, draft: Path, candidate: str):
    """Write the candidate to its source path and run the byte gate.

    Returns ``(outcome, report, rc, gate_out)``. The report's presence is the source of truth:
    the gate writes it only after a successful compare, so no report means the candidate did
    not compile (rc 3) or the gate errored.
    """
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(candidate)
    report_path = layout.work / "bytegate" / f"{entry['module']}_{entry['addr']}.report.json"
    report_path.unlink(missing_ok=True)
    rc, gate_out = run_subprocess(gate_argv(layout, entry, body, report_path))
    report = json.loads(report_path.read_text()) if report_path.exists() else None
    outcome = ("match" if report["ok"] else "mismatch") if report is not None else "error"
    return outcome, report, rc, gate_out


def process(entry: dict, entries: list[dict], layout: Layout, args, model,
            raw_text: bytes | None = None, feedback: "Feedback | None" = None) -> str:
    """One loop iteration. Returns 'match' | 'mismatch' | 'error' | 'dry-run'.

    A deterministic **template** (``tools/ledger/templates.py``) is tried first: it needs
    neither the context bundle nor the model, so a structural leaf skips both. The gate still
    decides; on a template miss the model is asked as a fallback, so this never regresses.

    ``feedback`` (a retry only) is the previous attempt's divergence, passed into the prompt so a
    retry edits rather than resamples; it is recorded (``feedback_used``) for auditability.
    """
    module, addr, name = entry["module"], entry["addr"], entry["name"]
    body, extent_source = resolve_body(layout, entry, args.body)

    draft = ensure_under(safe_draft_path(entry, layout.src_root), layout.src_root)
    if draft.exists() and not args.force:
        raise ValueError(f"{draft} exists (use --force to overwrite)")

    # 1. template (no bundle, no model) — propose; the gate disposes.
    raw_body = complexity.body_of(raw_text, addr, body) if raw_text is not None else None
    hit = templates.propose_rule(raw_body, name) if raw_body is not None else None
    candidate = hit[2] if hit else None
    source = "template" if candidate is not None else "model"

    if args.dry_run:
        if hit is not None:
            print(f"--- template for {name} (rule #{hit[0]}: {hit[1]}, "
                  f"{body} B, {extent_source}) ---")
            print(candidate)
        else:
            print(f"--- prompt for {name} ({body} B, {extent_source}) ---")
            print(build_prompt(entry, build_bundle_text(layout, entry, args, body), feedback))
        return "dry-run"

    # 2. model — only when no template fired.
    completion = prompt = None
    if candidate is None:
        candidate, completion, prompt = ask_model(entry, layout, args, model, body, feedback)
        if not candidate.strip():
            print(f"{name}: empty candidate from the model")
            return "error"

    # 3. write and verify (the gate is the only writer of verify=match).
    outcome, report, rc, gate_out = write_and_gate(entry, layout, body, draft, candidate)

    # 4. a template that missed falls through to the model, so the path never regresses.
    if outcome != "match" and source == "template":
        candidate2, completion2, prompt2 = ask_model(entry, layout, args, model, body, feedback)
        if candidate2.strip():
            candidate, source = candidate2, "model"
            hit = None                     # the rule missed; this is a model attempt now
            completion, prompt = completion2, prompt2
            outcome, report, rc, gate_out = write_and_gate(entry, layout, body, draft, candidate)

    # 5. record the attempt (append-only, parent-linked) — every attempt is kept.
    record = {
        "module": module, "addr": addr, "name": name, "body": body,
        "extent_source": extent_source, "outcome": outcome, "gate_rc": rc, "source": source,
        "model": completion.model if completion else "template",
        "prompt_tokens": completion.prompt_tokens if completion else None,
        "completion_tokens": completion.completion_tokens if completion else None,
        "latency_s": completion.latency_s if completion else 0.0,
        "prompt_sha256": prompt_fingerprint(prompt or ""),
        "gate_output": gate_out.strip()[-4000:],
    }
    if feedback is not None:
        record["feedback_used"] = True
    if hit is not None:
        record["template_rule"] = {"n": hit[0], "name": hit[1]}
    if report is not None:
        record["gate_status"] = report["status"]
        record["diff_count"] = report["diff_count"]
        record["diff_words"] = report.get("diff_words", [])
    stored = attempts.append(attempt_store(layout), record, candidate_text=candidate)

    # 6. bank a near miss (strictly-improving), and keep src/ matched-only.
    if outcome == "match":
        stamp = f"template rule #{hit[0]}: {hit[1]}" if hit else source
        print(f">>> MATCH  {name}  ({stamp})  -> {draft}  (attempt {stored['id']})")
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
                  one=process, raw_text: bytes | None = None) -> tuple[str, int]:
    """Run one entry up to ``args.attempts`` times, stopping on a match.

    Returns ``(outcome, attempts_used)``. Every attempt is recorded (parent-linked) by
    ``process``; a transport or bundle error counts as an attempt and is retried, since a
    runaway generation or a cold-load timeout is often transient. ``--dry-run`` previews once.

    Between attempts the previous attempt's divergence is threaded back in as ``feedback`` so a
    retry revises the last candidate instead of resampling an identical prompt (disable with
    ``--no-feedback``). Retrying also stops early once a mismatch reproduces the *same*
    divergence as the attempt before it — the feedback moved nothing, so further tries are waste.
    """
    outcome = "error"
    used = 0
    store = attempt_store(layout)
    feedback = None
    prev_words: list | None = None
    enabled = getattr(args, "feedback", True)
    for _ in range(max(1, args.attempts)):
        try:
            outcome = one(entry, entries, layout, args, model, raw_text, feedback)
        except (attempts.AttemptError, bundle.BundleError, model_client.ModelError,
                ValueError) as e:
            print(f"error: {entry['name']}: {e}", file=sys.stderr)
            outcome = "error"
        used += 1
        if outcome in ("match", "dry-run"):
            break
        if not enabled:
            continue
        try:
            record = attempts.latest_for(store / "log.jsonl", entry["module"], entry["addr"])
        except attempts.AttemptError:
            record = None
        feedback = feedback_from_record(record, store)
        words = feedback.diff_words if feedback else None
        if outcome == "mismatch" and words and words == prev_words:
            print(f"    stall: {entry['name']} repeated the same divergence; stopping early",
                  file=sys.stderr)
            break
        prev_words = words if words else prev_words
    return outcome, used


if __name__ == "__main__":
    raise SystemExit(main())
