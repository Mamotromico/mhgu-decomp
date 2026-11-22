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
  reconciler plus the CI invariant validator (`tools/ledger/validate.py`) keep it honest. The entry
  *set* remains the stable denominator; only status attributes change per match.
- **Status is not a funnel.** A single lifecycle enum cannot express "matched but not linked",
  "linked but generated", or "behaviour-matched, deliberately not enrolled" — and the two published
  metrics (*Progress metrics*) need different evidence. Status is therefore **four orthogonal
  axes**:

| axis | values | written by | meaning |
| --- | --- | --- | --- |
| `verify` | `none`, `behaviour`, `match` | byte gate | quality of the reconstruction; `behaviour` = equivalent but **not** byte-identical |
| `gate` | `""`, `raw`, `reloc`, `link` | byte gate / stub check | **provenance** of a `verify=match`: byte-identical compare, at least one address-dependent word verified through its relocation (*Gate provenance*, below), or an `import-stub` body derived from the GOT map (*Import stubs*, below) |
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
include(e)    := e.kind not in (external, import-stub)   # not source-reconstructed
counted(e)    := include(e) and not is_alias(e)          # honesty guard, below
decompiled(e) := counted(e) and e.verify == match
behaviour(e)  := counted(e) and e.verify == behaviour
built_stub(e) := e.kind == import-stub and e.verify == match   # link output, see below
done(e)       := decompiled(e) and link_build.region_ok(e)

Decompiled = |decompiled| / |counted|
Linked     = |done|       / |counted|
```

**`import-stub` is a kind, not a match.** A linker-generated GOT import stub is real
`.text` at a real address, but no C source produces it, so it leaves the denominator the
way an external does — while keeping its `addr`/`block`/`size` so the block partition
stays gapless. It carries `gate=link`, its own `built_stub` bucket, and is never counted as
decompiled. See *Import stubs are link output* below.

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

### Gate provenance (the `gate` axis)

A per-function claim is only as strong as the comparison behind it, and after the
relocation-aware diff lands there are two of them. `gate` records which one produced a match:

| value | meaning |
| --- | --- |
| `""` | no match — the only value a `verify ≠ match` entry may carry |
| `raw` | every compared word was byte-identical to the original |
| `reloc` | at least one address-dependent word (a branch/call immediate, or a literal-pool word) was verified through its relocation and the rest byte-compared |

**Why it is stored while `reloc` is not.** The distinction is derivability: `reloc` is a pure
function of the built image, so storing it would duplicate the build. `gate` records *how a
verdict was reached*, which cannot be recovered from the verdict or the image — without it a
match proven by resolving relocations would be indistinguishable from a byte-identical one, and
the near-miss/closeness numbers from the two regimes would silently mix.

**Enforced, not merely documented.** `ledgerlib.set_fields` writes `verify` and `gate` in one
line-surgical rewrite, so no reader observes a match without its provenance; and
`tools/ledger/validate.py` rejects a `match` with an empty `gate`, a non-match carrying one, an
unknown value, and any `gate` on an external. The gate's JSON report (`--report`) carries the
same value, so the loop records it in the attempt log too.

**Migration.** The column was added to the frozen seed once, mechanically: `raw` for the 2,316
entries already `verify=match` (they were all byte-identical), `""` everywhere else. No other
field changed.

**The literal-pool half needs the GOT map.** A branch relocation names its callee directly, so
the gate can resolve it from the ledger alone. A literal-pool word is different: `R_ARM_GOT_PREL`
names a **GOT slot**, and the linked word is `GOT(symbol) + addend − P` — so verifying one needs a
slot → symbol map. `tools/ledger/gotmap.py` builds it from the image's own dynamic metadata
(`MOD0` → `.dynamic` → `DT_REL`/`DT_JMPREL`/`DT_SYMTAB`) and reproduces the GOT extent from
`DT_PLTGOT` + `DT_INIT_ARRAY`, matching the range the Switch loader constructs. Only
`R_ARM_GLOB_DAT` and `R_ARM_JUMP_SLOT` fill a slot with a symbol address (`R_ARM_ABS32` patches
data words — vtables — and `R_ARM_RELATIVE` carries no symbol), so the map is 706 slots for the
image's 761 imports; the other 55 imports never receive one.

**Two kinds of slot, two ways to name them.** An *import* slot is named by the dynamic
relocation that fills it. An *internal* slot has no relocation — the static link resolved it —
but it **holds the object's address**, so the address names it as `D_<addr>`. That is what makes
a literal-pool word verifiable: `R_ARM_GOT_PREL` is patched to `GOT(symbol) + addend − P`,
where the addend is the object's own in-place word, and the comparison is then byte-exact.
The bundle annotates the same target (`; = 0x… -> D_…`) and a conditional prompt section tells
the model to declare the object rather than inline its address; without that the model emitted
a constant and the indirection was missing.

One extent rule follows from this: the inventory's body is *instructions only*, while the
compiler puts the literal pool inside the function's section. The loop decodes each reference
PC-relative literal load and extends the instruction extent through alignment bytes and every
referenced pool word (`complexity.function_extent`). That validated extent is passed as
`--body`; the ledger partition and reference block are bounds only. Missing reference bytes,
unaligned or out-of-partition pool targets, and candidates with a different length fail closed.
No comparison uses the candidate's length to accept a matching prefix.

**Import calls go through PLT stubs, not the symbol.** The image calls an import through a
12-byte stub in `.text` (`add r12, pc, #hi`; `add r12, r12, #lo`; `ldr pc, [r12, #off]!`), whose
computed address is a GOT slot. Decoding the idiom gives slot → stub; inverting it through the
map gives **import → stub** (695 imports, one stub each), which is the address the original
linked a `bl` to — the gate therefore resolves `bl <import>` against the stub map instead of
refusing it. 7,085 pending functions call an import. The same names are merged into the bundle's
name table, so a candidate is shown `; -> sqrtf` rather than `; -> plt_613efd58`.

### Matched-corpus regression baseline

`tools/ledger/revalidate.py` re-runs the byte gate over every `verify=match` source. It
does not edit the ledger; its purpose is to expose regressions in already-banked source.
The 22 clang 4.0.1 compiler residuals documented in `AGENTS.md` are therefore represented
explicitly in `config/main/revalidate-known-residuals.tsv`, rather than being folded into
an unexplained failure count.

A baseline row pins only `(module, addr, gate status, diff_count)` — no instruction bytes
are committed. Exact rows classify as `known-residual`; any other failure, a baseline
entry that now matches (`resolved-residual`), or a baseline address absent from the
selected results is reported separately and makes revalidation exit non-zero. A
module/limit run checks only baseline entries selected by that subset. Passing
`--known-residuals ""` restores the strict no-accepted-failures mode for experiments
that intentionally use a different profile. Thus an accepted residual remains visible,
but a changed residual cannot hide a new regression.

### Import stubs are link output

The same 12-byte stubs are also **symbols in `.text`** — one per import, 674 of them at the end
of the block. They are not compiled code: the linker emitted them, and the slot a stub jumps
through holds an address the loader resolves in *another module*. No C source can produce them,
so under the per-function gate they could never match (they absorbed 3,209 model attempts — 20 %
of the budget — at a 0 % ceiling, and because near-miss ranking sorts by closeness they sorted to
the front of the queue).

They are therefore **`kind=import-stub`**, excluded from the denominator like externals but
keeping `addr`/`block`/`size` so the partition still tiles the block:

- **Derived, not decompiled.** `tools/ledger/importstub.py` re-encodes the body from
  `(stub address, GOT slot)` alone — the split of the distance into the linker's three
  immediates, with *every* valid modified-immediate encoding enumerated and the reference bytes
  choosing — and accepts the row only when a candidate reproduces the reference exactly. A stub
  no split reproduces stays `verify=none` and is reported.
- **`gate=link`** is the provenance, and it is reserved for this kind; `validate.py` enforces
  that nothing else can carry it and that a stub can carry nothing else.
- **Reported separately.** `ledgerlib.built_stub` is its own bucket, so "674 stubs reproduced"
  can never be read as 674 decompiled functions. The decompiled figure is unchanged by them.
- **Not a link reproduction either.** Reproducing the *link* would need the vendor linker and
  its exact GOT slot assignment (measured: neither GNU `ld` nor `lld` reproduces it — see
  `tools/build/linkcheck.py`). Deriving the body from the recorded slot is what is achievable
  and it is what is verified here.

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

`tools/ghidra/InventoryExport.java` (driven by `tools/ghidra/inventory.sh`) writes five
deterministic TSVs into the git-ignored `baserom/work/inventory/` — a **draft** that seeds,
never replaces, the ledger:

| file | purpose | columns |
| --- | --- | --- |
| `inventory.tsv` | cut-point candidates → manifest | `addr kind size name block class source name_class thunk entry exported noncontig` |
| `inventory.nested.tsv` | reference-only symbols → review table | `addr kind name block source name_class parent` |
| `inventory.gaps.tsv` | uncovered initialized ranges → `D_<addr>` blobs | `block class addr size` |
| `inventory.externals.tsv` | imports (parsed from `.dynsym`) → `external` kind | `name bind` |
| `inventory.blocks.tsv` | memory-block extents → closes each block's partition | `block class addr size` |

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

### Ledger — concrete schema (committed)

The first committed ledger is generated by `tools/ledger/gen_ledger.py` into
`config/<module>/ledger.tsv` — one module, `main`, for the seed (the image has no overlays, so
`(module, addr)` needs no further split; a later split is a column edit, never a rename).
Columns, with the mandatory header row:

| column | meaning |
| --- | --- |
| `module` | module key (`main`) |
| `addr` | 8-hex image address (empty for externals) |
| `kind` | `function` \| `data` \| `external` |
| `name` | ledger identity: `func_<addr>` / `D_<addr>`, or a discovered name reproduced verbatim |
| `block` | memory block (`.text`/`.rodata`/`.data`/`.bss`); empty for externals |
| `group` | translation-unit membership; seeds as the entry's own name (one-function-per-file) |
| `size` | bytes; the block *partition* (below); empty for externals |
| `name_class` | `discovered` \| `generated` |
| `bind` | ELF binding, externals only (`LOCAL`/`GLOBAL`/`WEAK`) |
| `guess` | `0`/`1` — a *guessed* real name (never a placeholder) |
| `verify` | `none` \| `behaviour` \| `match` |
| `gate` | `""` \| `raw` \| `reloc` (empty unless `verify=match`) |
| `review` | `generated` \| `reviewed` |
| `enroll` | `rombytes` \| `complete` (empty for externals) |

`size` is the **block partition**, not Ghidra's body length. Within a block each cut point owns
the bytes up to the next cut point; gap blobs are cut points too, so an un-symbolised region
stays its own entry and stops a neighbour's growth (the last entry in a block is bounded by the
block end from `inventory.blocks.tsv`). This is required because Ghidra reports a function's
length as the *span* between its
first and last instruction: a non-contiguous body over-covers the function that begins in its
hole (1,057 draft overlaps) and leaves the interior literal-pool/jump-table bytes untilled
(2.7 MB of unclaimed `.text`). Deriving extents from the next cut point is what makes the
ledger disjoint *and* complete — every content block becomes an exact partition.

Status seeds at `verify=none` / `gate=""` / `review=generated` / `enroll=rombytes`; `reloc` is
derived by the link build and never stored. The ledger is a **frozen seed**: the generator writes it once
and refuses to overwrite an existing file (barring an explicit `--force`), because the authored
status axes must survive; CI is gated instead by the invariant validator
(`tools/ledger/validate.py`). The generator is content-only (metadata blocks dropped),
materialises `content` gaps as `D_<addr>` blobs, closes each content block's partition (head and
tail) from `inventory.blocks.tsv`, appends externals, and is a near-identity mapping of the
export so a diff shows exactly where a human overrode the draft.

### Symbol & data naming

Names are **discovered, not invented**. An unknown symbol keeps an address-encoded
placeholder until its real name is understood, and renaming is a ledger edit — never a
second symbol (see *Symbol identity & segmentation*).

- **Unknown code:** `func_<8hex>`, full base kept — e.g. `func_60001234`.
- **Linker import stubs:** `plt_<8hex>` — e.g. `plt_613f18d0`. They are neither code nor
  data: the name says the body is a GOT jump stub, so nobody mistakes one for a function
  (`kind=import-stub`, see *Import stubs are link output*).
- **Unknown data:** `D_<8hex>` — e.g. `D_6172f000`. The `func_`/`D_`/`plt_` triple marks
  *kind* (code vs. data vs. link output).
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
- **`src/` is matched-only.** A candidate that misses the current gate is not a build input:
  it is appended to the attempt log, upserted into the near-miss bank under its eval pin,
  and removed from `src/`. Re-gating such a banked candidate can still promote it later,
  because only the gate writes `verify=match`. A source with no ledger row has no authoritative
  gate extent and is archived as an orphan, not presented as reconstructed code.
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
  C. This is the sm64ds `enroll.py` shape. **Built:** `tools/build/linkcheck.py` assembles the
  inferred image — the original bytes everywhere, each matched function's compiled bytes at
  its own address with its relocations resolved the same way the gate resolves them (ledger
  address, PLT stub, GOT slot) — and compares the result to the original over every byte,
  naming the entry that owns a mismatch.
- **Why substitution and not `ld`.** A literal link cannot reproduce this image. It is
  position-independent, so a compiled function's `R_ARM_GOT_PREL` makes the *linker* allocate a
  GOT entry, at an address the linker chooses. Measured: `arm-none-eabi-ld -T script` places
  `.got.plt` immediately after `.text` (`0x60000028`), where the original has it at
  `0x61838000`. Neither GNU ld nor lld exposes the original's slot assignment, so byte-identical
  output is unreachable by linking; substitution applies the *original's* layout instead.
- **`rombytes` by default; `complete` on review.** A `src/` file's build input is the original
  bytes until its function matches, then flips to our compiled object — the promotion bridge
  already recorded under *File layout & generated build*.
- **Rejected — a committed `.s` (Model A).** Keeping an assembly listing of the original in
  the repo would commit bytes derived from the binary (a hygiene violation, see
  [`AGENTS.md`](../AGENTS.md)) and would need a proven AArch32 reassembler; neither is acceptable.

Precedent: OdysseyDecomp / Lego City (stubs; address-agnostic per-function `tools/check`);
sm64ds `tools/enroll.py` (`rombytes`/`complete`); nx-decomp-tools `delinks` for the
relocation-checked end state.

Implemented by `tools/ledger/` — `bytegate.py` (the gate: compile one function, diff it against
the original), `validate.py` (the ledger's invariants, the CI gate), `report.py` (the
decomp.dev/objdiff progress export), and `ledgerlib.py` (the schema and the one shared matched
predicate). The compiler pin lives in `config/toolchain.json`.

The reconstruction tree is seeded under `src/<module>/<group>.cpp` (committed) with a
committed `include/` tree for declarations. Its build inputs are **generated from the ledger**
by `tools/build/gen_compile_db.py` — the sole writer of `build/compile_commands.json` (which
activates clangd) — using the shared layout in `config/build.json`; the gate reads the same
include dirs so it compiles a candidate exactly as the build does.

The declaration tree is seeded by `tools/build/seed_externals.py`: a demangle pass over the
ledger's externals writing `include/generated/externals.tsv` (the review catalog) and
`include/generated/externals.hpp` (compilable Phase A `asm`-pinned candidates for the subset
whose types are expressible today — no return types, no class types). Both are deterministic
functions of the ledger with a CI `--check`. The reconstruction loop that *produces* candidates
is designed — not yet built — in [`llm-harness-design.md`](llm-harness-design.md).

### Progress metrics (two numbers)

Progress is reported as **two independent metrics**:

- **Decompiled** — from the committed ledger: the entries that meet the shared "matched"
  predicate. Requires no build.
- **Linked** — a whole-image comparison of the built output against the original (the
  relocation/link check, plus a first-mismatching-byte locator). Requires a build. Implemented
  as `tools/build/linkcheck.py`; it reports the first differing address and the ledger entry
  that owns it, and its `--report` payload carries the per-entry `linked` set that
  `report.py --link-report` publishes as the Linked figure (per-entry, because substitution
  makes each contribution independent).

The ledger metric is the published, continuously-reported number; the linked metric is the
end-state gate. The predicate's parts — the externals exclusion, the alias/zero-size guard, and
the `behaviour` exclusion — are defined once in *Status layer & the shared "matched" predicate*.

Precedent: decomp.dev's decompiled-vs-linked split; sm64ds "matched" vs "byte-verified".

**Export — the decomp.dev / objdiff report.** `tools/ledger/report.py` renders the ledger as an
objdiff `Report` (JSON, `version: 2`) — the exact format decomp.dev's bot ingests from a GitHub
Actions artifact named `<version>_report` (its `report.json`). The mapping *is* the predicate
above, so nothing is hand-authored: the site's **decompiled** figure is `matched_* ← decompiled`,
and **fully linked** is `complete_* ← enroll = complete` (the build-input axis; the derived
whole-image `reloc` check refines it at build time). Categories are modules (`main`); per-unit
detail is opt-in (`--units`), because the ledger's one-function-per-file default makes `group`
one-per-function and the full unit list hundreds of MB.

Byte accounting distinguishes **partition size** from **verified extent**. Total code/data keep
the ledger partitions, preserving the stable block-tiling denominator. Matched and complete
code/data instead sum the exact extents established by the gate: instruction spans plus any
referenced literal-pool words for functions, and inventory extents (or exact materialized gap
sizes) for data. `report.py` reads the NSO, `inventory.tsv`, and `inventory.gaps.tsv` directly
without Ghidra; a missing or partition-inconsistent matched extent is an error, never a silent
partition fallback. The same extent rule applies to top-level, category, unit, and item sizes.

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
