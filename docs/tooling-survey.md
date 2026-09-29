# Prior-art tooling survey (Phase 3 groundwork)

A living reference: what other matching decomps do that we might borrow, grouped by
project, with a suggested action per item. The survey below is the pool we refine from
while Phase 3 tooling takes shape — it is not itself a decision list. Confirmed decisions
are recorded in the section immediately below; when a point is adopted, promote it to its
own doc (or the relevant `tools/` README) and record the outcome here.

## Confirmed decisions

Decisions the project owner has signed off, with the reasoning kept next to each so it is
not re-litigated later. Everything not listed here is still open. *(This section is the
record of decisions and is deliberately not carrying status markers — every entry here is,
by definition, adopted.)*

### Function ledger

**Decision (2026-09-29):** a **committed, typed symbol ledger**, keyed by `(module, addr)`,
with **externals identified** as a first-class kind.

Rationale and shape:

- **Committed** — lives in git, not a generated artifact, so it is a *stable* denominator
  (unlike a linker map, a disassembler dump, or a `src/` directory scan).
- **Typed** — each entry carries a *kind* (function vs. data vs. external) plus attributes
  such as size (and arch), so a single artifact can both describe symbols and drive the
  build.
- **Keyed by `(module, addr)`, never `addr` alone** — overlays reuse base addresses across
  time, so a bare address can name two different symbols. This is not optional.
- **Externals as a first-class kind** — SDK / vendored symbols (our `nn::` surface) are
  recorded so references resolve, but excluded from the progress denominator.
- **Single source of truth** — the denominator for every progress number, and the universe
  the worklist, near misses, and claims are derived from.

Precedent: sm64ds `config/**/symbols.txt` (dsd format) for the typed, module-keyed ledger;
sm64ds `External` class and OdysseyDecomp `no_object_check_for` for the externals concept.

Still open (not yet decided): how status sits on top of the ledger (separate layer vs.
baked into entries), and the alias / shared-"matched" honesty guards.

## How to read this

Each bullet carries a **status** (a coloured circle, reflecting the project owner's
disposition toward it so far) and an **action tag** (how the idea would transfer):

| Status | Meaning |
| --- | --- |
| ⚫ | **Identified / considered** — noted, no decision taken. |
| 🔴 | **Considered but discarded** — deliberately not adopting. |
| 🟡 | **Partially adopted** — some of the idea is in use. |
| 🟢 | **Adopted** — in use (and, where it belongs, recorded under Confirmed decisions). |

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
- ⚫ **study — Ghidra as a draft generator only.** `tools/ghidra/DecompDump.java` writes
  `<addr>.c`; it is "scaffolds we hand to the LLM tier", never the identity authority.
- ⚫ **adopt — conservative re-symbolisation.** `tools/import_symbols.py` only renames slots
  still called `func_<addr>`, only at exact function starts; the rest land in
  `symbols/verified.tsv`. Inventing a name mid-blob "would resplit the data segment."

### Progress & honesty

- ⚫ **adopt — canonical DB derived from committed data only.** `tools/chaos_db_ci.py` runs
  with no ROM, no compiler, no local ledger; CI regenerates `chaos-db.json` per push and
  every surface reads that one file.
- ⚫ **adopt — README progress auto-written between `<!-- progress:start/end -->` markers**
  (`tools/progress.py`).
- ⚫ **adopt — publish "matched" and "byte-verified" side by side**, as two distinct numbers.
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
- ⚫ **adopt — promotion bridge** (`tools/enroll.py`): each `src/` file is written into
  `delinks.txt` as `rombytes` (build uses ROM bytes) or `complete` (build compiles ours).
  Idempotent. This is a generated→reviewed migration mechanism in concrete form.

### Skip

- 🔴 **skip — their `src/`-layout machinery** (`tools/srcpath.py`, `unnamed/<module>/`, cohort
  placement). It exists to fix a mess created *after* ~11k files went flat; we should fix
  layout up front instead.
- 🔴 **skip — mwcc-specific concepts** (`dcd` transcriptions, mwccarm flags, D0/D1/D2
  isolation). ARM9/mwccarm world; only the anti-gaming *principle* transfers.
- 🔴 **skip — the full ~100-script ecosystem** (treemap, atlas, coddog, coin ledger).

---

## `sotn-decomp` (layout & diffing)

- ⚫ **study — `splat` config as the single declaration of segments/splits**
  (`config/splat.*.yaml`). Declarative splitting, one file to rule the tree. Confirm
  AArch32 support before committing to splat.
- ⚫ **adopt — clean, shallow `tools/` layout** — easy to read, easy to extend.
- ⚫ **study — `asm-differ` integration** for the human-facing line-level diff (the companion
  to our byte gate).
- ⚫ **study — frogress** (below) as a progress dashboard; they are a reference adopter.
- ⚫ **study — decomp-permuter** in the last-mile loop.

---

## `OdysseyDecomp` (closest Switch analog)

- ⚫ **adopt — per-function status enum** (`data/file_list.yml`):
  `Matching / NonMatchingMinor / NonMatchingMajor / NotDecompiled / Wip`. A *graded* status,
  not just pass/fail — useful for our behaviour-match tier.
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
- ⚫ **study — `viking`'s data-tracking concepts.** ADRP-based for AArch64; we would need
  AArch32 equivalents for `adr` and literal pools.
- 🔴 **skip — as-is adoption.** Hardcodes `arch='aarch64'`, `R_AARCH64_*`, 64-bit ELF,
  `0x10`-byte PLT entries, `ADDRESS_BASE=0x71_0000_0000`.

---

## `pret` (pokeemerald / pokefirered) — conventions

- ⚫ **adopt — canonical naming scheme.** `func_XXXXXXXX`, data labels, `g`/`s`/`D_` prefixes —
  predictable, greppable, mapfile-checkable.
- ⚫ **study — unmatched-code fallback** (an `.s` kept alongside unmatched C, so the build
  stays green with partial progress).
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

---

## `sbergeron42/ssbu-decomp`

- ⚫ **lesson — document *which* code resists stock Clang** (some SDK internals). Sets
  expectations and gives us a place to record compiler-internal residuals — pairs with
  sm64ds's `floor` marks.

---

## `Lego-City-Undercover-Decompilation`

- ⚫ **study — third-party Switch C++ matching decomp build recipe.** CMake + Ninja,
  `ToolchainNX64.cmake`, `tools/config.toml`, musl sysroot. The most direct build-system
  precedent for our pinned clang and C++17 target.

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
  output; icing once we have a stable number to publish.

---

## Cross-cutting patterns worth naming explicitly

- 🟡 **One artifact owns identity** (the ledger); **one file owns the published number** (the
  canonical DB); **every tool imports the same "matched" predicate.** Divergence between
  tools is the specific failure mode sm64ds most aggressively defends against *(the ledger
  half is adopted; the canonical-DB and shared-predicate halves are not yet)*.
- ⚫ **Separate "who is right" from "who claims"** — verification is independent of the solver.
- ⚫ **Generated ≠ reviewed is a state machine, not a folder convention** (sm64ds `enroll.py`
  `rombytes`→`complete`; the n64-family nonmatching `.s` fallback).
- ⚫ **Pre-resolve everything a solver would otherwise have to look up** (the worklist) — the
  biggest cost lever in the whole corpus.

---

## Candidate priorities (not yet decided)

In leverage order, if/when we start building:

1. 🟡 Committed `(module, addr)` ledger with a status enum. *(sm64ds + OdysseyDecomp)*
2. ⚫ Deterministic progress from committed data + one canonical DB + auto-written README
   block. *(sm64ds)*
3. ⚫ Pre-resolved worklist. *(sm64ds)*
4. ⚫ Independent verify-and-bank. *(sm64ds)*
5. ⚫ Near-miss bank + eval pin. *(sm64ds)*
6. ⚫ Promotion state machine `rombytes` → `complete`. *(sm64ds + n64-family)*
7. ⚫ CMake + Ninja build. *(Lego City / OdysseyDecomp)*
8. ⚫ Relocation-aware link check shaped like nx-decomp-tools. *(study)*

## Known gap

Every mature reference starts from an **auto-splitter** (dsd, splat) that produces its
ledger. Neither is confirmed for **AArch32**, and our target is the *AArch32* Switch
variant. So the practical first move is a Ghidra-side inventory export
(`(address, size, name)` over `.text`) — which requires one cached auto-analysis run, kept
**additive** so `poc/run.sh` (intentionally `-noanalysis`) is unchanged.

## Open questions

- Draft `docs/ledger-and-progress.md` sketching (a) the `(module, addr)` ledger format +
  status enum + `External` class and (b) committed-data progress derivation adapted to our
  pinned-clang gate? *(Design doc only, no code.)*
- Fix the `(module, addr)` key in the PoC now (overlay-safe), or leave the PoC as-is and
  make it Phase-3 groundwork?

---

*Refine in place. When a point is adopted, promote it to its own doc and record the
outcome here.*
