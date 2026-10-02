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

**Resolved — status is baked into entries.** An entry carries identity *and* status (see
*Status layer & the shared "matched" predicate*); there is no separate sidecar. The entry *set*
stays the stable denominator; only the status attributes churn. The honesty/link attributes
(`guess`, `lazy`) remain entry properties.

### Status layer & the shared "matched" predicate

Per-symbol status is **baked into the ledger entry** — not a separate sidecar. The entry is the
single committed record of both *identity* and *status*, keyed by the same `(module, addr)`.

- **One committed artifact.** Status shares the ledger's `(module, addr)` key, so there is no join
  to reconcile and no second file to drift. Cost accepted: the ledger's git history mixes identity
  edits with match progress — that churn is mechanics, not meaning, and the single-writer
  reconciler plus CI `--check` (see *File layout & generated build*) keep it honest. The entry
  *set* remains the stable denominator; only status attributes change per match.
- **Status is not a funnel.** A single lifecycle enum cannot express "matched but not linked",
  "linked but generated", or "behaviour-matched, deliberately not enrolled" — and the two published
  metrics (*Progress metrics*) need different evidence. Status is therefore **four orthogonal
  axes**:

| axis | values | written by | meaning |
| --- | --- | --- | --- |
| `verify` | `none`, `behaviour`, `match` | byte gate | quality of the reconstruction; `behaviour` = equivalent but **not** byte-identical |
| `review` | `generated`, `reviewed` | reviewer | readability tier (*Generated vs. reviewed code*); `reviewed` preserves the byte match |
| `enroll` | `rombytes`, `complete` | reconciler | build input — original bytes vs. our compiled object |
| `reloc` | *(derived)* | link build | relocation/link check — **computed, never authored** |

- **`enroll` is two-valued; the unmatched case is a project-level mode.** A project-wide
  `build_mode ∈ {C, B}` (see *Unmatched-function fallback*) decides what an unmatched symbol
  resolves to: a **stub** in Mode C, `rombytes` in Mode B. Either way
  `enroll = complete ⇔ verify = match` and the region is reloc-clean — a `behaviour` match is
  never enrolled as compiled, or it would poison the whole-image Linked metric.
- **`reloc` / Linked are derived, not stored.** `AGENTS.md`'s per-function "done" includes the
  relocation/link check, but *Progress metrics* makes Linked a whole-image number; the link build
  computes it and the canonical DB joins it. Nothing here is hand-authored.
- **`guess` / `lazy` stay identity attributes**, not status — they gate naming/linking honesty,
  not matching.

**One shared "matched" predicate.** Every tool — the gate, the DB builder, CI — imports the *same*
predicate so the definitions cannot drift (sm64ds `bytegate.counts_as_matched`):

```text
include(e)    := e.kind != external                 # externals leave the denominator
counted(e)    := include(e) and not is_alias(e)     # honesty guard, below
decompiled(e) := counted(e) and e.verify == match
behaviour(e)  := counted(e) and e.verify == behaviour
done(e)       := decompiled(e) and link_build.region_ok(e)

Decompiled = |decompiled| / |counted|
Linked     = |done|       / |counted|
```

**Honesty guards** (settle the alias / shared-"matched" half):

- **Alias / zero-size dropped from both sides.** A second name at an existing `(module, addr)`, or
  a zero-size entry, counts in neither the numerator nor the denominator.
- **matched-but-unbuilt is surfaced.** `decompiled ∧ enroll ≠ complete` is reported as its own
  bucket, so a match is never inflated by code the build does not use.
- **`behaviour` never adds to Decompiled** — it is reported beside the match count.
- **`guess` / `lazy` are identity attributes**, not status.

Precedent: sm64ds `bytegate.counts_as_matched` (one shared predicate), `is_zero_size_alias` and
`enrollment_of` (the guards); sm64ds `tools/tiers.py` (distinct denominators, explicitly "not a
funnel").

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

### Inventory export — concrete schema

`tools/ghidra/InventoryExport.java` (driven by `tools/ghidra/inventory.sh`) writes four
deterministic TSVs into the git-ignored `baserom/work/inventory/` — a **draft** that seeds,
never replaces, the ledger:

| file | purpose | columns |
| --- | --- | --- |
| `inventory.tsv` | cut-point candidates → manifest | `addr kind size name block class source name_class thunk entry exported noncontig` |
| `inventory.nested.tsv` | reference-only symbols → review table | `addr kind name block source name_class parent` |
| `inventory.gaps.tsv` | uncovered initialized ranges → `D_<addr>` blobs | `block class addr size` |
| `inventory.externals.tsv` | imports (parsed from `.dynsym`) → `external` kind | `name bind` |

Classification rules (the export is the draft; the ledger generator is authoritative):

- **`kind ∈ {function, data}`** in `inventory.tsv`; **externals are a separate file**, not a
  `kind` value, because their schema differs (no size/block/addr).
- **`class ∈ {content, metadata}`** is a per-row block class, so the generator (and a human)
  can tell game image from linker plumbing without re-deriving it. Only `content` rows
  contribute to the progress denominator.
  - `content` — the game image: `.text`/`.rodata`/`.rodata.1`/`.data`/`.data.1`/`.bss`.
  - `metadata` — the ELF dynamic-linking blocks the loader *synthesises*
    (`.dynstr`/`.dynsym`/`.rel.dyn`/`.rel.plt`/`.hash`/`.gnu.hash`/`.dynamic`/`.got`/`.got.plt`/
    `.init_array`): regenerated by the link, never reconstructed from source, so the generator
    excludes them. The loader's synthetic `EXTERNAL` memory block (import stubs) is skipped
    entirely — those symbols are the `.dynsym` imports below.
- A **function** (any executable block) and **top-level data in a non-executable block**
  (`.rodata`/`.data`) are cut points. **Data living inside `.text`** (literal pools, jump
  tables) is reference material and lands in `inventory.nested.tsv` via the symbol pass.
- **Externals come from `.dynsym`, not the symbol table.** Auto-analysis *demangles* external
  symbols, so the exact Itanium-mangled name — the identity the ledger reproduces, since it
  pins the signature — survives only in the ELF dynamic string table. The export parses
  `.dynsym`/`.dynstr` directly and emits every `SHN_UNDEF` entry with its ELF binding
  (`LOCAL`/`GLOBAL`/`WEAK`), which also supplies the external binding the ledger's relocation
  check needs. The mangled name encodes its own namespace, so no separate `library` column is
  required.
- The nested file is **symbol-table driven**: every program-space symbol that is *not* the
  primary symbol at a cut-point address — labels inside functions, aliases, params/locals,
  literal-pool labels. `parent` is the enclosing function entry (or empty). Struct/array
  *components* are a follow-up: they are `Data`, not symbols, and are not enumerated yet.
- `name_class` is `discovered` iff `Symbol.getSource()` is `IMPORTED` or `USER_DEFINED`,
  else `generated` (see *Symbol & data naming*).
- `thunk`/`noncontig`/`entry`/`exported` are booleans: `Function.isThunk()`, a body spanning
  >1 range, membership in the loader's external entry points, and `Symbol.isGlobal()`.
- **Gaps** are *initialized* bytes claimed by neither a function body nor a defined `Data`
  (uninitialized blocks — `bss`, the `EXTERNAL` block — are skipped: nothing to match); the
  generator fills the `content` ones as `D_<addr>` so the denominator is complete.
- One row per symbol; **aliases are not deduplicated** — alias resolution is the ledger
  generator's job.

The cold run performs a **full auto-analysis** (not `-noanalysis`); the export is meaningless
over an un-analysed program.

### Ledger & export format

The committed ledger and the Ghidra inventory export share **one line-oriented text format —
TSV, one record per line, with a mandatory header row** — so the ledger generator is a
near-identity mapping of the export and a `diff` of the two shows exactly where a human
overrode the draft.

- **TSV, because the readers are three.** The same rows are produced by a Ghidra script,
  consumed by the ledger generator, and reviewed by a human / `git diff`. TSV is the only format
  that serves all three: line-oriented, so `sort`/`awk`/`join`/`diff`/`wc -l` work and git review
  stays per-record; dependency-free to parse; and it needs exactly one invariant — **no tab or
  newline inside a field** — which Ghidra symbol names (including Itanium-mangled `_ZN2nn…`) never
  violate, asserted by the producer rather than trusted.
- **A header row is mandatory.** It makes the schema self-describing and lets columns be added
  (status axes, `group`, …) without silent column-position drift.
- **CSV is rejected.** Its quoting rules break the line-oriented shell tooling for no benefit —
  we have no spreadsheet-interop requirement.
- **JSONL is the escape hatch for heterogeneous records only.** The nested-symbol table's rows
  differ per kind (jump table vs. literal pool vs. vtable/RTTI vs. struct field), so *that* file
  may switch to self-describing JSONL if a fixed column set becomes sparse-and-ugly; the uniform
  tables stay TSV. Not load-bearing — the nested table never reaches the manifest.
- **SQLite is a working store at most.** A git-ignored, regenerable DB is welcome as an
  *analysis* aid (relational queries over symbols ⋈ references), never as a committed artifact —
  it is binary and not reviewable.

Precedent: sm64ds `config/**/symbols.txt` (dsd text format) + `symbols/verified.tsv`;
pret/zeldaret line-oriented symbol lists.

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
- **The Ghidra raw name is provenance, not identity.** Ghidra's auto-names (`FUN_`, `DAT_`,
  `byte_`, `word_`, …) are kept **verbatim in the draft export** — they carry real signal
  (found-vs-invented, and a debugging key for draft↔ledger round-trips) — but are **never** the
  ledger name, which stays `func_<addr>` / `D_<addr>`. The prefix encodes Ghidra's *inference*
  (`DAT_`/`byte_` = data typing, `FUN_` = function detection) and can shift across analysis runs,
  so adopting it would contradict *Ghidra & output policy* ("Ghidra never decides … names"). An
  entry may carry the raw name as **provenance** — a non-symbol attribute that never enters the
  namespace, so it cannot become an alias. Discovered names (`dynsym`/RTTI) are reproduced
  verbatim whether or not Ghidra prefixes them, so the draft's discovered-vs-generated
  classification reads `Symbol.getSource()` and symbol type, **not** the prefix string.

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

Open: the two-adjacent-functions experiment that detects real TU coupling. (The state set the
ledger records is resolved — see *Status layer & the shared "matched" predicate*; the fallback
for unmatched functions is resolved — see *Unmatched-function fallback* below.)

### Unmatched-function fallback (staged)

The fallback for code we have not yet matched is **staged**, not a single mechanism, and it
is the same axis as the generated/reviewed state. The active stage is the project-wide
`build_mode` — `C` (stubs) now, `B` (byte substitution) at the end state — which decides what an
unmatched symbol's `enroll` resolves to (see *Status layer & the shared "matched" predicate*).

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
end-state gate. The predicate's parts — the externals exclusion, the alias/zero-size guard, and
the `behaviour` exclusion — are defined once in *Status layer & the shared "matched" predicate*.

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
