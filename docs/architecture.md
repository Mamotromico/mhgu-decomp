# Architecture

The authoritative model of the reconstructed project: what the source of truth is, how
symbols are identified and segmented, how files and the build are derived from that, and
where the tooling boundaries sit. Every section here is a **confirmed decision** (signed off
by the project owner), with its rationale kept alongside so it is not re-litigated later.
Everything not recorded here is still open.

This is the **promoted** record. The prior-art pool it was refined from — with its per-item
status circles and action tags — remains in [`tooling-survey.md`](tooling-survey.md); a
point moves from there to here when it is adopted.

## Project model

### Symbol ledger

The ledger is a **committed, typed symbol ledger** keyed by `(module, addr)`, with
**externals as a first-class kind**. It is the universe every other mechanism draws from.

- **Committed** — lives in git, not a generated artifact, so it is a *stable* denominator
  (unlike a linker map, a disassembler dump, or a `src/` directory scan).
- **Typed** — each entry carries a *kind* (function vs. data vs. external) plus attributes
  such as size (and arch), so a single artifact can both describe symbols and drive the
  build.
- **Keyed by `(module, addr)`, never `addr` alone** — overlays reuse base addresses across
  time, so a bare address can name two different symbols. This is not optional.
- **Externals as a first-class kind** — SDK / vendored symbols (our `nn::` surface) are
  recorded so references resolve, but excluded from the progress denominator.
- **Externals carry linker attributes.** A binding such as weak / `lazy` is a property of the
  external's entry, consumed by the relocation/link check — a *linking* fact, not a progress
  status.
- **`Library` is not a new concept.** OdysseyDecomp's `Library` status *is* our `external`
  kind above — provided, not verified, and excluded from the denominator.
- **Single source of truth** — the denominator for every progress number, and the universe
  the worklist, near misses, and claims are derived from.

Precedent: sm64ds `config/**/symbols.txt` (dsd format) for the typed, module-keyed ledger;
sm64ds `External` class and OdysseyDecomp `no_object_check_for` for the externals concept.

Open: how *progress* status sits on top of the ledger (separate layer vs. baked into
entries) — the honesty/link attributes (`guess`, `lazy`) are settled as entry properties, and
the two published metrics are settled (*Progress metrics*), but the matched/unmatched status
layer itself is not — and the alias / shared-"matched" honesty guards.

### Symbol identity & segmentation

The ledger owns segment boundaries, so re-symbolisation is **conservative**: we **rename
existing placeholder entries only** and never **introduce** a boundary from an import.

- A symbol entry in a manifest of this shape *is* a cut point — recording an address that
  is not already a committed boundary **is** the split. Nobody has to "decide" to split.
- **Inner/nested symbols** (struct members, vtables, RTTI/typeinfo, jump tables, literal
  pools) are legitimate facts but are **reference material, not split points**; they go to a
  review table (the `symbols/verified.tsv` analogue) and never the manifest.
- Rationale: a nested entry resplits a segment, changing the generated files, alignment, and
  the progress denominator, and orphaning already-matched work.

Precedent: sm64ds `tools/import_symbols.py` + `symbols/verified.tsv`.

### Segmentation seed (Ghidra inventory export)

The committed ledger is **seeded from a deterministic Ghidra inventory export**, not from a
third-party auto-splitter.

- **One export, both kinds.** A single cached auto-analysis run yields `(addr, size, kind,
  name)` for **functions and in-program data** (`.rodata`/`.data`) alike — code and data are the
  same segmentation problem, and one export covers both.
- **Reference-driven, therefore a draft.** Data is enumerated only where a *reference* points at
  it (a relocation, a constant-address load, a recovered table entry), so computed-offset blobs
  can be missed and boundaries inferred. The export **seeds** the ledger; the ledger stays
  authoritative (see *Ghidra & output policy*).
- **No third-party auto-splitter.** splat (and the dsd family) are dropped from the critical
  path: splat's AArch32 support is unconfirmed and its proven ground is MIPS-family. Its one
  transferable idea — a declarative segment/split config — is convenience, not a seeder.
- **In-program data only; romfs/assets are out of scope.** The match target is `main.nso`;
  romfs assets live in a separate NCA that `main.nso` does not contain, so no asset pipeline is
  required.

Precedent: sm64ds `dsd` and sotn `splat` auto-splitters (the mechanism *not* adopted); Ghidra
headless inventory (per *Ghidra & output policy*).

### Symbol & data naming

Names are **discovered, not invented**. An unknown symbol keeps an address-encoded
placeholder until its real name is understood, and renaming is a ledger edit — never a
second symbol (see *Symbol identity & segmentation*).

- **Unknown code:** `func_<8hex>`, full base kept — e.g. `func_60001234`.
- **Unknown data:** `D_<8hex>` — e.g. `D_6172f000`. The `func_`/`D_` pair marks *kind* (code
  vs. data).
- **Scope prefixes** `g_` (external linkage) and `s_` (file-local / internal linkage) are
  added once linkage is known. They sit on a different axis from the placeholder, so a
  symbol can be `D_<addr>` (unknown) or `gName` / `sVar_<addr>` (scope known, name not yet).
- **Internal symbols** (`s_`) live in a **module namespace**, one per module. This is free:
  internal names are byte-invisible — no ABI mangling, no dynamic relocation — so it costs
  nothing at the match while resolving the overlay address collisions that `(module, addr)`
  keying makes possible.
- **Externals and class members are discovered, not chosen.** Their mangled name is already
  in the binary (`dynsym`, and RTTI/typeinfo in `.rodata`), so it is reproduced exactly; a
  chosen namespace or a guessed name on such a symbol is a *match-breaker*, not an organizer.
  Reproducing it also pins the signature — mangling encodes parameters and `const` — so a
  correct name doubles as a correctness check on the reconstruction.
- **An unrecoverable name is marked, not silently invented.** When a symbol's real
  class/namespace cannot be recovered from the binary (a stripped class with no RTTI), the
  entry carries a **`guess`** attribute on its declared reconstruction, so a guessed name is
  never mistaken for a discovered one. This keeps *discovered, not invented* honest — a
  guessed name does not claim to have been discovered — and costs nothing at the match, since
  an internal name is byte-invisible.

Precedent: pret `func_XXXXXXXX` + `g`/`s`/`D_` prefixes; zeldaret `func_08000000` /
`D_08000000` / `sXxx`; sm64ds `func_<addr>` inside the ledger; OdysseyDecomp `guess` flag.

### File layout & generated build

Translation-unit membership is a **ledger column**, not a filename or folder convention;
files are **primarily one function per file** and are **merged only when the original
grouping is required for codegen**; the build inputs are **generated from the ledger**,
never hand-maintained.

- **TU membership is data.** A function's translation unit is a `group` field on its
  `(module, addr)` entry. Merging is a ledger edit, not a rename storm — identity never
  came from the filename, so a merged TU (two functions, one file, a name that is neither
  symbol) is expected, not a surprise.
- **Per-function default; merge on evidence.** One function per file guesses nothing and
  isolates codegen. Merge only when the original grouping is *required* to reproduce
  codegen — an inlined helper, shared constants — decided by experiment, not by guesswork.
- **The build is a function of the ledger.** The source list *and* the linker script are
  generated, so a merge never produces a hand-edited CMake/Ninja diff. With
  `-ffunction-sections -fdata-sections` the linker places — and byte-substitutes — per
  function, so TU grouping affects only codegen, never what the link emits.
- **One reconciler is the sole writer**, moving/merging files and regenerating the build
  inputs idempotently; CI runs it `--check` and fails on drift.
- **Generated ≠ reviewed is ledger state, not a folder.** A folder-per-state split was
  considered and **rejected**: one folder expresses one axis, per file only, and a merged TU
  has mixed state — plus it re-introduces path churn. State lives in the ledger and is
  surfaced by tooling / dashboards instead.

Precedent: sm64ds `tools/enroll.py` (`delinks.txt` as `rombytes`/`complete`),
`tools/srcpath.py` (one central resolver; *"placement follows migration, it does not lead
it"*), `tools/import_symbols.py` + `symbols/verified.tsv`; nx-decomp-tools `delinks`.

Open: the state set the ledger records, and the two-adjacent-functions experiment that
detects real TU coupling. (The fallback for unmatched functions is resolved — see
*Unmatched-function fallback* below.)

### Unmatched-function fallback (staged)

The fallback for code we have not yet matched is **staged**, not a single mechanism, and it
is the same axis as the generated/reviewed state.

- **Now — Model C (stubs).** While coverage is partial, an unmatched callee is *declared, but
  not defined*, so the tree still compiles and links as a normal developer executable.
  Matching is then a **per-function claim** (an address-agnostic instruction diff), independent
  of "does it build". This is the OdysseyDecomp / Lego City model and our on-ramp.
- **End state — Model B (byte substitution).** To reach our "done" (a linked image with a
  relocation/link check), unmatched *regions* are filled from the original binary **by the
  build itself** — object-level byte substitution (`rombytes` / `delinks`), never reconstructed
  C. This is the sm64ds `enroll.py` shape.
- **`rombytes` by default; `complete` on review.** A `src/` file's build input is the original
  bytes until its function matches, then flips to our compiled object — the promotion bridge
  already recorded under *File layout & generated build*.
- **Rejected — a committed `.s` (Model A).** Keeping an assembly listing of the original in
  the repo would commit bytes derived from the binary (a hygiene violation, see
  [`AGENTS.md`](../AGENTS.md)) and would need a proven AArch32 reassembler; neither is acceptable.

Precedent: OdysseyDecomp / Lego City (stubs; address-agnostic per-function `tools/check`);
sm64ds `tools/enroll.py` (`rombytes`/`complete`); nx-decomp-tools `delinks` for the
relocation-checked end state.

### Progress metrics (two numbers)

Progress is reported as **two independent metrics**:

- **Decompiled** — from the committed ledger: the entries that meet the shared "matched"
  predicate. Requires no build.
- **Linked** — a whole-image comparison of the built output against the original (the
  relocation/link check, plus a first-mismatching-byte locator). Requires a build.

The ledger metric is the published, continuously-reported number; the linked metric is the
end-state gate.

Precedent: decomp.dev's decompiled-vs-linked split; sm64ds "matched" vs "byte-verified".

## Constraints

### Ghidra & output policy

Ghidra is driven **only** through pinned, committed **headless scripts**; **GhidraMCP is
dropped**. All Ghidra **output** is **draft content** and is **never committed**.

- **Headless only, agent-facing.** No live query path for agents. Human interactive
  analysis remains available via `ghidra-gui.sh` (noVNC/X11) — the ban is on treating a
  live, non-deterministic query as truth, not on looking.
- **Output is a draft, never truth.** Decompiled C, disassembly listings, memory-block
  dumps and logs are generated into the git-ignored `baserom/work/` tree and never
  committed. Ghidra never decides symbol identity, boundaries, names, or the progress
  denominator.
- **Content vs. metadata.** Binary *content* (bytes, disassembly text) is never committed;
  binary *metadata* may be, but only in its reviewed/committed form. A deterministic
  inventory export may **seed** the committed ledger (see *Segmentation seed*); the ledger
  itself stays authoritative and hand-owned.
- **One cold analysis, many warm queries.** Full auto-analysis runs once into a cached
  Ghidra project under `baserom/work/`; all later work is targeted script runs against it.
  Ghidra's value declines as coverage grows — it stays for unexplored regions, anomalies,
  and data.

Precedent: sm64ds `ghidra/DecompDump.java` ("scaffolds we hand to the LLM tier", never the
identity authority).

### Frozen PoC snapshot

`poc/` is a **frozen snapshot** of the Phase-1/2 validation experiment.

- **No further edits.** It is not maintained or extended.
- **Not a structural template.** Phase 3 tooling is built fresh, with its own layout; the
  PoC's structure (directory layout, bare-`addr` keying) is *not* to be copied.
- **Soft reference only:** its byte-gate *mechanics* (`poc/lib/cmpbytes.py`,
  `poc/lib/matchdiff.py`) may be consulted, but nothing else.

This also resolves the open question about fixing the `(module, addr)` key in the PoC: **no —
leave it as-is**; the fix belongs in the Phase-3 ledger.
