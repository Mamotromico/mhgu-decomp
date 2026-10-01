# Prior-art tooling survey (Phase 3 groundwork)

A living reference: what other matching decomps do that we might borrow, grouped by
project, with a suggested action per item. The survey below is the pool we refine from
while Phase 3 tooling takes shape — it is not itself a decision list. Adopted decisions are
promoted to [`architecture.md`](architecture.md); when a point is adopted, record it there.

## How to read this

Each bullet carries a **status** (a coloured circle, reflecting the project owner's
disposition toward it so far) and an **action tag** (how the idea would transfer):

| Status | Meaning |
| --- | --- |
| ⚫ | **Identified / considered** — noted, no decision taken. |
| 🔴 | **Considered but discarded** — deliberately not adopting. |
| 🟡 | **Partially adopted** — some of the idea is in use. |
| 🟢 | **Adopted** — in use (and, where it belongs, recorded in [`architecture.md`](architecture.md)). |

| Tag | Meaning |
| --- | --- |
| **adopt** | Idea transfers essentially as-is to our AArch32 / clang-5.0.1 / MHGU setting. |
| **adapt** | Right idea, but needs rework for our target, language, or workflow. |
| **study** | Design reference only — do not expect to lift the code. |
| **skip** | Explicitly *not* worth importing; recorded so we don't re-litigate it. |

The status circle and the tag are complementary: a **tag** says *how* an idea would
transfer, a **status** says *where it stands right now*. They can differ — e.g. an `adopt`
idea that is still only identified shows as ⚫.

Line-level script/flag names in the referenced repos drift over time; the *architectures*
are what should be judged stable. Where a claim is tied to a specific file, the file is
named so it can be re-checked against upstream.

---

## `sm64ds-decomp` (the most automated pipeline)

Provenance: ARM9 / mwccarm, but the pipeline shape is the richest of any reference.
Files referenced below live under their `tools/`.

### Enumeration & identity

- 🟢 **adopt — committed typed ledger as the single universe.** e.g.
  `func_02001a64 kind:function(arm,size=0x40) addr:0x02001a64` (`config/**/symbols.txt`,
  dsd format). This is the denominator for *every* progress number.
- 🟢 **adopt — key by `(module, addr)`, never `addr` alone.** Documented in their
  `tools/modules.py`: overlays reuse base addresses across time, so "anything that records
  matches must key by `(module, addr)`, never addr alone." *This is the one detail that is
  not optional for us.* Our PoC currently keys by bare `addr`.
- 🟢 **adopt — Ghidra as a draft generator only.** `tools/ghidra/DecompDump.java` writes
  `<addr>.c`; it is "scaffolds we hand to the LLM tier", never the identity authority.
- 🟢 **adopt — conservative re-symbolisation.** `tools/import_symbols.py` only renames slots
  still called `func_<addr>`, only at exact function starts; the rest land in
  `symbols/verified.tsv`. Inventing a name mid-blob "would resplit the data segment."
  *(Accepted; see *Symbol identity & segmentation* in
  [`architecture.md`](architecture.md).)*

### Progress & honesty

- ⚫ **adopt — canonical DB derived from committed data only.** `tools/chaos_db_ci.py` runs
  with no ROM, no compiler, no local ledger; CI regenerates `chaos-db.json` per push and
  every surface reads that one file.
- ⚫ **adopt — README progress auto-written between `<!-- progress:start/end -->` markers**
  (`tools/progress.py`).
- 🟢 **adopt — publish "matched" and "byte-verified" side by side**, as two distinct numbers.
  *(Accepted; see *Progress metrics* in [`architecture.md`](architecture.md).)*
- ⚫ **adopt — one shared definition of "matched"** (`bytegate.counts_as_matched`, via
  `tools/asm_policy.py`), so separate tools cannot drift.
- ⚫ **adopt — honesty rules.** `bytegate.is_zero_size_alias` drops second names from the
  numerator *and* the denominator; `enrollment_of` splits matched-but-unbuilt into
  `enrolled / unenrolled / no_block`.
- ⚫ **adapt — three tiers MATCHED / CONVERTED / LINKED** (`tools/tiers.py`), explicitly *not*
  a funnel, with distinct denominators. CONVERTED is scored on comment-masked code against
  five pinned regexes (`real_name`, `no_raw_offset`, `no_unk_field`, `no_codegen_trick`,
  `no_mangled_refs`). The *anti-gaming principle* transfers; the specific regexes are
  mwcc-flavoured and must be re-derived for clang/ARM32.

### The automated crack loop

- ⚫ **adopt — pre-resolved worklist** (`tools/worklist.py`): per-function target bytes (hex)
  plus annotated disassembly where **every `bl`/`blx` resolves to the callee name and every
  pc-relative load to its pool value/symbol**, each callee's signature, and N few-shot
  matched siblings sharing the mnemonic sequence. Their stated goal: the difference between
  a cheap agent ("here is the function, write the C") and an expensive one ("go figure out
  what this calls").
- ⚫ **adopt — independent verify-and-bank** (`tools/bank.py`): recompile and recompare
  outside the solver. Never trust the solver's own claim of a match.
- ⚫ **adopt — near-miss bank with strictly-improving upsert** (`tools/nearmiss_db.py`):
  `closeness = (divergences, |cand_size − size|)`, an **eval pin** (`eval_pin.json`
  fingerprinting compiler + metric, warning on staleness), and `floor` marks for
  compiler-internal residuals.
- ⚫ **adopt — append-only attempt log, parent-linked tree** (`tools/match_attempts.py`):
  records *every* attempt, including `no_progress`.
- ⚫ **study — claims over git refs** (`tools/classqueue.py`): parentless commits so a second
  claimant's push is always non-fast-forward (they document the bug where pushing `HEAD`
  lets everyone think they won). Clever; defer until we are multi-contributor.
- 🟢 **adopt — promotion bridge** (`tools/enroll.py`): each `src/` file is written into
  `delinks.txt` as `rombytes` (build uses ROM bytes) or `complete` (build compiles ours).
  Idempotent. This is a generated→reviewed migration mechanism in concrete form.
  *(Accepted; see File layout & generated build.)*

### Skip

- 🟡 **partially adopted — their `src/`-layout machinery** (`tools/srcpath.py`,
  `unnamed/<module>/`, cohort placement). The cohort / `unnamed` heuristics are skipped: they
  exist to fix a mess created *after* ~11k files went flat, and we fix layout up front
  instead. The underlying principle **is** adopted — one central resolver, and placement
  follows the ledger, never the reverse. *(See File layout & generated build.)*
- 🔴 **skip — mwcc-specific concepts** (`dcd` transcriptions, mwccarm flags, D0/D1/D2
  isolation). ARM9/mwccarm world; only the anti-gaming *principle* transfers.
- 🔴 **skip — the full ~100-script ecosystem** (treemap, atlas, coddog, coin ledger).

---

## `sotn-decomp` (layout & diffing)

- 🔴 **skip — `splat` as an auto-splitter.** AArch32 support is unconfirmed and its proven
  ground is MIPS-family; our segmentation seed is a Ghidra inventory export, not a third-party
  splitter (see *Segmentation seed* in [`architecture.md`](architecture.md)).
- ⚫ **study — `splat`'s declarative segment/split config** (`config/splat.*.yaml`): one file
  declaring every segment and split. The idea, not the tool.
- ⚫ **adopt — clean, shallow `tools/` layout** — easy to read, easy to extend.
- ⚫ **study — `asm-differ` integration** for the human-facing line-level diff (the companion
  to our byte gate).
- ⚫ **study — artifact-derived progress** (`tools/progress.py`): the denominator is the build's
  linker map (`mapfile_parser`), and the "matched" bit is the absence of a nonmatchings `.s` /
  `.NON_MATCHING` symbol. Publishes per commit to frogress + Discord + a self-hosted site. This
  is the reference for our **Linked** metric surface; its `.s`-presence status bit and
  build-derived denominator are the Model-A mechanism we rejected (*see Progress metrics*).
- ⚫ **study — decomp-permuter** in the last-mile loop.
- ⚫ **note — AGPL-3.0.** Compatible with our GPL-3.0 (any copied files stay AGPL). Prefer
  study/reimplement over vendoring.

---

## `OdysseyDecomp` (closest Switch analog)

The nearest analog to us: a Switch **C++** matching decomp sharing our toolchain family
(upstream Clang), our language, and — crucially — a build model that is **not an image**. Its
build (`add_executable` over reconstructed `src/*.cpp` + vendored lib sources) produces a
**developer executable**: a normal ELF whose job is to (1) force the whole reconstruction to
compile and link as a type/consistency check, (2) supply symbols and a compile database for
editors, and (3) host the per-function gate. It is *not* the NSO, is not byte-matched, and is
not playable. The load-bearing reframe: **in this model, building ≠ matching** — matching is a
separate per-function claim, and the build proves only "it compiles".

- 🟢 **adopt/adapt — stubs as the linkability fallback.** Non-inline callees that are not yet
  reconstructed are simply *declared, not defined*, so the tree still links. This is the
  Model C fallback and our on-ramp to Model B; a committed `.s` fallback is rejected. *(Accepted;
  see *Unmatched-function fallback* in [`architecture.md`](architecture.md).)*
- ⚫ **adopt — per-function status enum** (`data/file_list.yml`):
  `Matching / NonMatchingMinor / NonMatchingMajor / NotDecompiled / Wip`. A *graded* status,
  not just pass/fail — useful for our behaviour-match tier, and an input to the *Decompiled*
  metric. Of these, `Library` is not a new concept: it *is* our `external` kind (see *Symbol
  ledger* in [`architecture.md`](architecture.md)).
- 🟢 **adopt — the `guess` name-honesty flag.** `guess = the symbol is a guess and does not
  appear in the target executable` — recorded so a guessed name is never mistaken for a
  discovered one. *Accepted as a ledger attribute; see *Symbol & data naming* in
  [`architecture.md`](architecture.md).*
- 🟢 **adopt — the `lazy` linker-binding flag** (weak / lazy symbol). A real linker attribute;
  it belongs as a property on an external entry, consumed by the relocation/link check.
  *(Accepted; see *Symbol ledger*.)*
- ⚫ **study/adapt — `tools/check` / `asm-differ` as the per-function gate.** A concrete
  reference implementation of the human-facing line-level diff (see the diff ecosystem below).
  Note it is **address-agnostic** — the guide says to ignore `adrp`/`bl`/`b` address
  differences — which makes it *weaker* than our linked-image gate. Adopt the mechanism; keep
  our stricter gate.
- ⚫ **study — one source, two build modes.** `NON_MATCHING` / `MATCHING_HACK_*` macros isolate
  matching-only hacks behind a platform define, so a single tree yields both a functional build
  and a matching build. The same *shape* as our generated-vs-reviewed split, but expressed as a
  compile switch rather than ledger state.
- 🟢 **adopt — exclude SDK/vendored paths from object checks** (`tools/config.toml`
  `no_object_check_for = ["sead/","NintendoSDK/","eui/","agl/"]`). Maps onto our `nn::`.
- ⚫ **study — devcontainer + CMake+Ninja+ccache** build precedent.
- ⚫ **study — vendored `tools/common`** (from open-ead/nx-decomp-tools) as a migration model;
  see the AArch64 caveat below.
- ⚫ **study — legal/dumping wording** in their README.

---

## `open-ead/nx-decomp-tools` (reference architecture only)

- ⚫ **study — relocation-aware reference checking.** Exactly the *shape* our Phase-3 link
  gate needs (`bl`, literal pool, GOT).
- ⚫ **study — `listsym` / `check` tooling; function metadata + status tracking.**
- 🔴 **skip — porting `viking`'s data tracking.** ADRP-based for AArch64; the segmentation
  seed (Ghidra inventory export — see *Segmentation seed*) already recovers in-program data from
  relocations and references.
- 🔴 **skip — as-is adoption.** Hardcodes `arch='aarch64'`, `R_AARCH64_*`, 64-bit ELF,
  `0x10`-byte PLT entries, `ADDRESS_BASE=0x71_0000_0000`.
- ⚫ **note — MIT-licensed (leoetlino).** The only repo in the open-ead family that grants a
  reusable license, so it is the one part we may freely adopt/port (subject to the AArch32
  caveat above); the source libraries below are unlicensed and off-limits for reuse.

---

## `pret` (pokeemerald / pokefirered) — conventions

- 🟢 **adopt — canonical naming scheme.** `func_XXXXXXXX`, data labels, `g`/`s`/`D_` prefixes —
  predictable, greppable, mapfile-checkable. *(Accepted; see *Symbol & data naming* in
  [`architecture.md`](architecture.md).)*
- 🔴 **skip — committed `.s` unmatched-code fallback.** Rejected: it would commit bytes derived
  from the original binary (a hygiene violation, see [`AGENTS.md`](../AGENTS.md)) and would need
  a proven AArch32 reassembler. Our fallback is staged instead — stubs now, object-level byte
  substitution later *(see *Unmatched-function fallback* in [`architecture.md`](architecture.md))*.
  The mapfile-progress and `-Werror` ideas below are unaffected.
- ⚫ **study — mapfile-driven progress** — derive matched/unmatched from the linker map rather
  than a hand-maintained list.
- ⚫ **study — strict `-Werror` + fixed warning set** so generated code cannot silently change
  codegen.

---

## `zeldaret` (oot / mm) — mature matching layout

- ⚫ **study — established `src/` + `asm/` + `include/` + `tools/` discipline**, with module
  boundaries mirroring the ROM's overlay structure.
- ⚫ **study — permuter + asm-differ as first-class repo tools.**
- ⚫ **study — split/build manifest discipline** (different toolchain; the discipline is what
  transfers).

---

## `open-ead/sead` — validation precedent

- ⚫ **lesson — upstream Clang *can* match Switch code.** `MATCHING_HACK_NX_CLANG` shows how
  to isolate the few spots that need help. Directly supports our de-facto-pin thesis and our
  eventual behaviour-match tier.
- ⚫ **lesson — unlicensed, so reference only.** sead ships **no `LICENSE`** (like the rest of
  the open-ead source family); see *The open-ead ecosystem* below. We take declarations from
  our own binary, never their text.

---

## The open-ead ecosystem (declaration source, not a dependency)

OdysseyDecomp and Lego City pull their "externals" from an open-ead library family: `sead`,
`agl`, `eui`, `NintendoSDK-NEX` (source), `nnheaders` (headers only), and `botw-lib-musl` (a
binary libc). Three facts govern how — and whether — we use it.

**We take declarations, not bodies.** The SDK/sead code MHGU statically linked is *already
inside* `main.nso`; a matching build byte-substitutes it (Model B) and never recompiles it. So
the ecosystem's only value to us is a head start on the `nn::` *declarations* our call sites
need. It is **not** a linkable SDK, and adopting it as one would be wrong.

**Their mangling is not our mangling.** Every repo targets **AArch64**; we are **AArch32**.
Itanium mangling encodes canonical types, so `size_t` mangles as `unsigned long` (`m`) on
LP64 but `unsigned int` (`j`) on ILP32 — any function taking a `size_t`/`ptrdiff_t`-style
parameter mangles differently for us. Our ground truth is our own binary: the exact `nn::`
symbols are in `main.nso`'s `dynsym`, so the workflow is **read the name from our binary, then
write a declaration that reproduces it** — never copy theirs.

**Licensing — unlicensed, not copyleft (verified).** `nx-decomp-tools` is MIT; `botw-lib-musl`
is MIT (but a binary build). `sead`, `agl`, `eui`, `NintendoSDK-NEX` and `nnheaders` ship **no
`LICENSE` file** — default copyright, all rights reserved, which is *more* restrictive than any
copyleft (copyleft at least grants permission with conditions; no license grants nothing). A
clean-room reconstruction is not the original's code, but it is still its own copyrighted,
separately-owned work — and here, an unlicensed one. So we neither vendor nor transcribe their
headers/source: we derive names from our own `dynsym` and treat their repos as a reading aid.
If we ever reuse text, it needs explicit permission + attribution.

---

## `sbergeron42/ssbu-decomp`

- ⚫ **lesson — document *which* code resists stock Clang** (some SDK internals). Sets
  expectations and gives us a place to record compiler-internal residuals — pairs with
  sm64ds's `floor` marks.

---

## `Lego-City-Undercover-Decompilation`

- ⚫ **study — third-party (non-Nintendo) Switch C++ matching decomp.** Same Model C build
  shape as OdysseyDecomp: `add_executable` over reconstructed `src/*.cpp` + `lib/nnheaders`,
  with `NON_MATCHING` / `MATCHING_HACK_*` compile defines (one source, functional vs. matching
  modes). A *developer executable*, never the image.
- ⚫ **study — pinned toolchain distribution.** CMake + Ninja, `ToolchainNX64.cmake`,
  `tools/config.toml`, musl sysroot; it pins a specific clang (3.9.1). Precedent for
  distributing our pinned clang/ld.lld as artifacts — the most direct build-system precedent
  for our pinned clang and C++17 target.

---

## Diff / permuter / dashboard ecosystem

- ⚫ **`asm-differ`** — **study/adapt.** Instruction-level diff between our `.o` and the
  original; complements `poc/lib/cmpbytes.py`. Confirm the AArch32 (`--arch`) objdump path.
- ⚫ **`reccmp`** — **study.** Symbol-level *scored* comparison (accuracy %) against a
  reference build; good for a per-module scoreboard. Heavyweight (needs symbols/PDB); not a
  byte-gate replacement.
- ⚫ **`decomp-permuter`** — **study.** Randomised last-mile matching; needs `import.py` and
  `permuter_settings.toml` (compiler/assembler commands). C-first; C++ support partial —
  relevant only once stragglers are the bottleneck.
- ⚫ **`decomp.me`** — **study.** Web scratchpad + scoring; can host our compiler preset for
  sharing single-function puzzles.
- ⚫ **`frogress`** — **study.** Self-hosted progress dashboard reading a project's progress
  output; the publish surface for our two metrics once we have a number to publish.
- ⚫ **`decomp.dev`** — **study (nice-to-have).** Public dashboard consuming a project's progress
  feed; the decompiled-vs-linked split is the UI shape our two metrics mirror.

---

## Cross-cutting patterns worth naming explicitly

- 🟡 **One artifact owns identity** (the ledger); **one file owns the published number** (the
  canonical DB); **every tool imports the same "matched" predicate.** Divergence between
  tools is the specific failure mode sm64ds most aggressively defends against *(the ledger and
  shared-predicate halves are now adopted — see *Status layer & the shared "matched" predicate*
  in [`architecture.md`](architecture.md); the canonical-DB half is not yet)*.
- 🟢 **Two progress numbers: decompiled (ledger) and linked (artifact).** The ledger number
  needs no build; the linked number is the end-state gate. *(Accepted; see *Progress metrics* in
  [`architecture.md`](architecture.md).)*
- ⚫ **Separate "who is right" from "who claims"** — verification is independent of the solver.
- 🟢 **Generated ≠ reviewed is a state machine, not a folder convention** (sm64ds `enroll.py`
  `rombytes`→`complete`). *(Accepted; folders rejected — see File layout & generated build and
  *Unmatched-function fallback*.)*
- ⚫ **Pre-resolve everything a solver would otherwise have to look up** (the worklist) — the
  biggest cost lever in the whole corpus.

---

## Candidate priorities (not yet decided)

The **segmentation seed** (Ghidra inventory export) is adopted and precedes everything below —
see *Segmentation seed* in [`architecture.md`](architecture.md).

In leverage order, if/when we start building:

1. 🟢 Committed `(module, addr)` ledger with a status enum. *(sm64ds + OdysseyDecomp)* —
   **promoted** to [`architecture.md`](architecture.md) → *Symbol ledger* / *Status layer & the
   shared "matched" predicate* (status baked into entries; four axes; one shared predicate).
2. ⚫ Deterministic progress from committed data + one canonical DB + auto-written README
   block. *(sm64ds)*
3. ⚫ Pre-resolved worklist. *(sm64ds)*
4. ⚫ Independent verify-and-bank. *(sm64ds)*
5. ⚫ Near-miss bank + eval pin. *(sm64ds)*
6. 🟡 Promotion state machine `rombytes` → `complete`. *(sm64ds + n64-family; the
   state-not-folders shape is adopted — see File layout & generated build.)*
7. ⚫ CMake + Ninja build. *(Lego City / OdysseyDecomp)*
8. ⚫ Relocation-aware link check shaped like nx-decomp-tools. *(study — the **Linked** metric; see Progress metrics in [`architecture.md`](architecture.md))*
9. ⚫ Model C per-function gate rig — stub callees, diff one function (`asm-differ`-style, cf.
   `poc/lib/matchdiff.py`) — staged toward Model B. *(OdysseyDecomp / Lego City)*

## Segmentation seed — resolved

Promoted to [`architecture.md`](architecture.md) → *Segmentation seed*. In short: the ledger is
seeded from a **Ghidra inventory export** covering functions **and** in-program data (one cached
auto-analysis run, kept *additive* so `poc/run.sh`'s intentional `-noanalysis` is unchanged). No
third-party auto-splitter (splat's AArch32 support is unconfirmed), and romfs/assets are outside
`main.nso` and out of scope.

---

*Refine in place. When a point is adopted, promote it to its own doc and record the
outcome here.*
