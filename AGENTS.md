# AGENTS.md

Guidance for coding agents (and any automated contributor) working on mhgu-decomp.

This file is a **living document** — it records conventions, pinned tooling, and
discoveries that agents must respect. Update it as the project learns things. It
complements [README.md](README.md): the README is for humans, this file is the
operational contract for automated work. Full evidence for the compiler findings lives
in [`docs/compiler-identification.md`](docs/compiler-identification.md); don't duplicate
it here.

---

## What this project is

A **decompilation** of *Monster Hunter Generations Ultimate* (Nintendo Switch): a
clean-room, buildable C++ source tree whose functions compile to **byte-identical**
machine code under the pinned toolchain (or as close as it allows). This is *not* a
normal software project — the original binary is the single source of truth, and every
change to translated C++ must be validated against it (see [Validation](#validation)).

## Core principles

1. **The binary is truth.** No "cleanup", refactor, or optimization that breaks
   byte-matching.
2. **Never invent behavior.** Every function must trace back to disassembly/decompiler
   output; don't guess what it "probably" does.
3. **One function at a time.** Small, verifiable units; prefer matching one function
   over touching many.
4. **Record findings** here or in `docs/` (compiler idioms, symbol naming, data layout).
5. **Byte-match first, readability second.** Some functions may only reach a
   *behaviour* match. Readability becomes the focus once most functions match (target
   ~90%). Tooling output that optimises only for a byte match may be unreadable, but
   must stay distinguishable from human-reviewed code (see below).

## README is human-facing — flag agent edits

Agent/LLM-written or -rewritten content in `README.md` must be wrapped in the review
markers `>🤖` (open) and `🤖<` (close) until a human reviews and adopts it (then the
markers are removed). Pure removals need no marker — they show up in the diff.

## Generated vs. reviewed code

- **Generated (byte-match-first)** — automated/LLM-assisted output whose only
  requirement is a byte match; may be unreadable.
- **Reviewed** — a human reworked generated code for readability *while preserving the
  byte match*.

The distinction is **ledger state, not a folder layout** (a folder split was considered
and rejected: one folder expresses one axis per file only, and merged translation units
have mixed state). The tier is recorded on the ledger entry and surfaced by tooling;
files stay one function per file, merged only when the original grouping is required for
codegen. See [`docs/architecture.md`](docs/architecture.md) → *File layout & generated
build*.

---

## Environment & pins

Ghidra and its Switch loader live **inside the devcontainer** (no host Java needed);
the devcontainer/Dockerfile is the source of truth for the toolchain. Details in the
README; the facts:

- **Ghidra 12.1.2** at `/opt/ghidra` (`GHIDRA_HOME`); **Java 21 JDK** at
  `JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64`.
- **Switch Loader** extension under `${GHIDRA_HOME}/Ghidra/Extensions/SwitchLoader`.
- Wrappers: `.devcontainer/scripts/ghidra-headless.sh` (automation), `ghidra-gui.sh`
  (GUI via noVNC/X11).
- **clang** is installed at `/opt/clang-4.0.1`, on `PATH` (with the `libtinfo.so.5` it
  needs). It ships bare; project target flags come from `config/toolchain.json`.

**Pinned versions — byte-matching (and the prebuilt loader) depend on exact versions.
Never change without explicit approval.**

| Component | Pin | Notes |
| --- | --- | --- |
| Ghidra | `12.1.2` | **Not** 12.1.4 — the prebuilt loader is built against 12.1.2. |
| Ghidra SHA-256 | `b62e81a0390618466c019c60d8c2f796ced2509c4c1aea4a37644a77272cf99d` | Verified in the Dockerfile. |
| Switch Loader | `1.6.1-c600d05-Ghidra_12.1.2` | Pin the full tag (`<ver>-<commit>-Ghidra_<ver>`). |
| Loader SHA-256 | `0bc6374c11cb7a1275a0eda22184b9b2efe5a9a7e415cc29361c334966c1f477` | Verified in the Dockerfile. |
| clang | `4.0.1` | The compiler pin (reproduction stand-in). |
| clang tarball SHA-256 | `ca48a4def4cbc9dd6af3f46ce1dc2bd903d26c7ad51387f57884ad1eaa58e42f` | Verified in the Dockerfile. |
| libtinfo5 | `6.1-1ubuntu1.18.04.1` | ncurses-5 ABI the pinned clang links against (Ubuntu 18.04 archive). |
| Base image | `ubuntu:24.04` | Batteries-included apt; size not a concern. |

Do not "upgrade" pinned tooling or add a guessed toolchain / a third clang without
explicit approval.

> **Ghidra project location:** keep the project under `baserom/ghidra/` — it embeds
> bytes derived from the original binary, and `baserom/*` is git-ignored wholesale. Run
> the headless import with `-noanalysis` against `baserom/main.nso`; logs go under
> `baserom/work/`.

---

## Architecture (confirmed)

**AArch32 (32-bit ARM)** — not the AArch64 Switch default. Two independent sources
agree: NPDM metadata (`Is64BitInstruction: false`,
`ProcessAddressSpace: AddressSpace32BitNoReserved`) and the Switch Loader's MOD0
heuristic (`NXOAdapter.isAarch32()` → `ARM:LE:32:v8:default`, image base `0x60000000`).
Corroborates the [Fexty12573/forge](https://github.com/Fexty12573/forge) lead
(devkitPro/devkitARM + `switch32.ld`).

`baserom/main.nso` (git-ignored) is a verified `NSO0` image — the **latest title
update** (`b3935415…645ef`). We target the update, not base `v0`: both report the
identical `SdkAddon Ver.: 4.4.1 (v67371264)` and an aligned `.text` diff shows the
update is an incremental patch over an otherwise-identical codebase (≈81% byte
overlap), so the compiler gives no reason to prefer base.

Memory map (base `0x60000000`):

| Block | Start | End |
| --- | --- | --- |
| `.text` | `0x60000000` | `0x613f1dec` |
| `.rodata` | `0x613f2000` | `0x613f206c` |
| `.rodata.1` | `0x61550ccb` | `0x6172e6fa` |
| `.data` | `0x6172f000` | `0x61837f28` |
| `bss` | `0x6184b000` | `0x62146788` |

The loader also processes the ELF dynamic relocation metadata (`.rel.dyn` at
`0x13F206C`, `.rel.plt`, `.init_array`, and a constructed `got` from `0x1838AE8` to
`0x1848900`) — the basis for the Phase 3 relocation/link check.

---

## Compiler & runtime (resolved — pin: clang 4.0.1)

The toolchain is a **de facto pin**, not the vendor's true toolchain (a NintendoSDK
build; unobtainable):

```text
Architecture:  AArch32 (32-bit ARM) — ARM:LE:32:v8, base 0x60000000
Language std:  C++17 (-std=c++1z)
Runtime/libc:  NintendoSDK 4.4.x (nn:: C++ API), libc++ (-stdlib=libc++)
Compiler:      clang 4.0.1 — the pin + one hidden backend flag; no stock config matches all probes
Float:         ARMv8-A FP + NEON (Cortex-A57 feature set) — hardfp ABI
```

**Build flags (the pin), from `config/toolchain.json`:**

```text
clang -target armv8a-none-eabi -mfpu=neon-fp-armv8 -mfloat-abi=hard \
      -O2 -fomit-frame-pointer -fPIC -fno-exceptions -fno-rtti \
      -ffreestanding -std=c++1z \
      -mllvm -pre-RA-sched=source
```

Key facts:

- **C++ is the target language.** Imports are the `nn::` C++ API in Itanium mangling;
  every Switch reference project is C++ (`sead`, BotW, SMO, SSBU, Lego City). Write
  `.cpp` with C-style bodies; use C++ features (exceptions, templates, vtables) only
  where the original forced them.
- **Upstream Clang, not the proprietary NX fork.** Matching Switch decomps build with
  stock Clang (OdysseyDecomp, Lego City — both 3.9.1 — and sead). clang 4.0.1 is the
  **only** supported pin; the former 5.0.1 secondary was retired (plan step 0.5).
- **No `-mcpu`.** `-mcpu=cortex-a57` was copied from AArch64 reference projects and is
  wrong for this 32-bit target; `-mtune` is inert in this backend. SoC is the Tegra X1
  (T210, "Erista": 4×Cortex-A57 + 4×Cortex-A53; A57 cluster only).
- **FPU: `-mfpu=neon-fp-armv8`** (the Cortex-A57 AArch32 feature set), **not**
  `vfpv4-d16`. The original `.text` provably contains instructions VFPv4 cannot emit:
  ARMv8-A FP (`vseleq/vselgt/vselge`, `vmaxnm/vminnm`, `vrintm/vrinta`, `vcvtp` —
  ~2,946 words in ~1,041 functions) and NEON (`vmax/vmin/vdup/vld1` in ~318 functions) —
  ~1,259 functions (2.93%) a VFP-only build can never match.
  `-mfloat-abi=hard`: floats cross the ABI in the VFP s-registers.
- **History:** the initial pin (clang 5.0.1 + `-hoist-cheap-insts=true` +
  `-pre-RA-sched=source`) structurally cannot reproduce the original's `bfc` (it emits
  `bic`), its if-conversion, and some scheduling (4,173 true-`bfc` ledger functions, of
  which 3,379 have only BIC-encodable masks — none ever matched under 5.0.1). 4.0.1
  reproduces all three, matched 2,354/2,376 (99.1%) of the then-matched corpus, and
  needs only `-pre-RA-sched=source`. No stock configuration matches all seven probes —
  positive evidence for a non-stock/fork AArch32 backend. The `-mllvm` flag is a hidden
  diagnostic that makes our build emit what the original emitted, not a real build
  setting. Evidence: [`docs/compiler-identification.md`](docs/compiler-identification.md).

### Accepted residuals (22, pinned in `config/main/revalidate-known-residuals.tsv`)

Re-deriving source shapes under 4.0.1 fixed 8 former mismatches — `func_6018e958`
(early-return form → `movne`), `func_6054ee64` (store the halfword before loading the
divisor), `func_6003b788` (nested `if`, not `continue`), `func_6080c93c` /
`func_6016b920` (in-place narrow-type inc/dec: `unsigned char x = field; x--;` defeats
the mask DAG-combine), `func_600a7e80` (a 4-byte `bx lr` stub with no source). **22
remain (10 `body-length`, 12 `mismatch`), all accepted:**

| Class | Addresses | Notes |
| --- | --- | --- |
| Predicated early return in a loop (7) | `6013fe3c` `604f8b78` `6050f78c` `6069d9e8` `6069ddfc` `6069eb18` `610b0960` | 4.0.1 if-converts a loop-exit `return` into `popcc {…,pc}`; the original branches. No source shape defeats it; only a global if-converter disable does, costing the common guards. `pop {…,pc}`-specific heuristic diff (the reference *does* if-convert leaf `bxne lr` guards). |
| Instruction ordering (5) | `602aa498` `602aa814` `6050c964` `60876a94` `610e897c` | Two independent loads/ops swapped. Statement reordering does not change SelectionDAG scheduling; no `-pre-RA-sched`/`-misched`/`-regalloc` knob matches. (A few used to be pinned with an `asm` barrier — withdrawn, demoted to unmatched.) |
| Multi-instruction predicated return (5) | `605bc604` `60627aac` `61122598` `613720ec` `605089e4` | The original predicates `ldrbne/movne/cmpne/bxne lr`; 4.0.1 branches (or predicates the other side). |
| Tail duplication / block placement (2) + stack-arg hoisting (2) | `6003bb78` (one branch byte only) `601cb7e8` / `601ac4d8` `60c17abc` | 4.0.1 hoists the 5th-argument load above the first store; duplications differ. `-disable-tail-duplicate` fixes these but drops the corpus to 2,290 — cannot be global. |
| 4.0.1-vs-5.0.1 DAG choice (1) | `60260440` | Predicates the else-body instead of the hoisted `mov`+`bxhi lr`. |

`func_6053a058` and `func_6018b110` mismatch since their `asm`-barrier "fixes" were
removed (a scheduler ordering diff; 7 spellings tried, none reproduces it) —
`verify=none`.

### Source shapes that fix "unmatchable" classes (verified 2026-11)

The masked-pointer class is a **source-shape** problem, not a compiler limit —
deterministic templates in `tools/ledger/templates.py`, documented in the loop prompt
(`tools/loop/run.py`). Measured on one 100-entry model-loop run: converted 8 further
entries to byte matches at zero model cost.

- **Masked pointer used as a base (`ldr` → `bfc` → address use).** The masked value is
  the *base*, so express it as a pointer: `*(float *)(v + 0x5c)`,
  `(unsigned)((char *)v + 0x40)`. As integer arithmetic (`return v + 0x40;`) clang
  folds the constant and emits `add` **before** `bfc`; the original is `bfc` then `add`.
  Templates `masked-pointer-add` (7/7), `masked-pointer-float` (1/1).
- **Conditional return guard (`bxhi lr`/`bxeq lr`/…).** For `if (idx > 7) return 0;
  return a[idx];` 4.0.1 if-converts the guarded body into `addls`/`ldrls` and folds
  `bx lr` — 24 B where the original branches (28 B). **No source shape restores the
  branch** (25 spellings tried: early-return, ternary, `if`/`else`, `goto`,
  `while`+`break`, `do`/`while(0)`, nested `if`, separate offset variable, `switch`,
  `volatile` load, `__builtin_expect` both probabilities, typed array indexing — all
  if-convert). Expected from the LLVM source: `isProfitableToIfCvt` charges the branch
  `+1 + MispredictionPenalty/10` vs predication's `NumCycles`, so a 2-instruction block
  with a 4-cycle load is "profitable" even at probability 1
  (`ARMBaseInstrInfo.cpp`, release_40). **Accepted residual**, behaviour-match at best.
  (A `guarded-word-index` template once claimed 18/18 here via a banned `asm` barrier —
  deleted; its 8 ledger rows `6005ceb4` `6013f6d4` `6013f6f0` `602768f4` `60276960`
  `60277394` `602773b0` `60282780` are demoted to `verify=none`.)
- **Pre-indexed writeback (`ldrh r2,[r0,r2]!`, `str r1,[r0,#0x18]!`).** Address
  computed, used *and* written back in one instruction. The C must update the pointer
  inside the expression **and then read it again**, or the writeback is dead and clang
  drops it (body one instruction short):
  `unsigned short v = *(unsigned short *)(p = (unsigned short *)((char *)p + 0x1a0));`
  followed by a use of `p`. Verified: `func_60501848` byte-matches on the first try
  from this shape (the model's `*(T *)((char *)p + imm)` never can). A post-indexed
  form (`[r0], #imm`) advances the pointer *after* the access. ~6,000 pending bodies
  contain a `!` writeback — the highest-yield shape in the queue; the loop detects it
  (`run.has_preindexed`) and injects `_PREINDEXED_SECTION`.

**Never `__builtin_memcpy(&w, char_ptr + off, 4)`.** clang cannot assume alignment
through a `char *` and emits four byte-sized loads (a 40 B body for a 16 B original).
Load through a typed pointer (`*(unsigned *)(p + off)`). This was the single most
expensive model mistake in the run; the prompt now warns against it.

The loop reports body sizes on a `body-length` verdict: the diff words cover only the
reference *prefix*, so without "20 B vs 16 B — 4 BYTES TOO LONG" the model cannot see
the surplus instruction to delete.

### Linker veneers are not functions (674 `import-stub` rows, 0.25% of the denominator)

`.text` end (`0x613efd58`–`0x613f1de0`) holds **674 twelve-byte GOT import stubs**:

```text
add  r12, pc, #0x400000  ; 4 MB page step (imm8=4, rot=6)
add  r12, r12, #imm      ; rotated immediate — the page offset
ldr  pc, [r12, #imm]!    ; pre-indexed .got.plt load straight into pc
```

Example (`613f18d0`): `r12 = 0x613f18d8 + 0x400000 + 0x47000 = 0x618388d8`; then
`ldr pc, [r12, #0x5c]!` reads `0x61838934` in `.got.plt`, holding `0x623cf000` — the
loader-resolved address of an imported function in another module. **No C source
produces these** (the slot value is a link/load-time fact about *other* modules), so
they can never byte-match — yet they consumed 3,209 model attempts (20% of the budget)
at a 0% ceiling, and sorted to the front of the near-miss queue. `complexity.is_veneer`
detects them byte-exactly and `gateable()` rejects them, so `--matchable` (default ON
since 2026-11) never selects one.

**Resolved (2026-11): `kind=import-stub`.**

- `kind=import-stub`, name `plt_<addr>`, `enroll=""` — excluded from the denominator
  (`ledgerlib.included`) while keeping `addr`/`block`/`size`, so the partition still
  tiles. Denominator 267,181 → **266,507**; the decompiled figure is untouched.
- `verify=match` / **`gate=link`** — reserved provenance. `validate.py` rejects
  `gate=link` on any other kind and any other gate on a stub.
- **Derived, not decompiled.** `tools/ledger/importstub.py` re-encodes the 12 bytes
  from `(stub address, GOT slot address)` alone — enumerating every valid
  modified-immediate encoding of the linker's three-step split, accepting only a
  candidate that reproduces the reference exactly. **674/674** currently derive;
  `--apply` is idempotent.
- `ledgerlib.built_stub` is its **own bucket** — "674 stubs reproduced" can never be
  read as 674 decompiled functions.

This is not a link reproduction: reproducing the *link* needs the vendor linker and its
GOT slot assignment (neither GNU `ld` nor `lld` reproduces it —
`tools/build/linkcheck.py`). After a re-seed or renamed import, re-run:
`python3 tools/ledger/importstub.py --check` (report) / `--apply` (stamp). Seeding
itself stays image-free — the retype is a post-seed step, documented in
`gen_ledger.py`.

### Re-gate stored candidates before believing a verdict

`baserom/work/attempts/log.jsonl` is **append-only history**, not current state: a
record's `MISMATCH` was issued by *whatever gate existed then*, and entries that later
matched keep their old failure rows. Two measured consequences:

- **Never compute a match rate from the log.** It reports stale failures and
  understates the result (log: 9,363 attempts / 2,238 matches on "plain" entries;
  ledger: 2,311 of 3,530 such entries matched).
- **A stored candidate may already match.** `tools/ledger/regate_candidates.py`
  recompiles the blobs under `baserom/work/attempts/main/<addr>/<id>.cpp` with the
  *current* pin and gate — free, no model calls; on the "plain" backlog it converted
  86/1,296 entries (6.6%). Run with `--update` to bank the winners (they keep their
  `src/` file). The raw-byte-gate era false-mismatched every non-leaf, so 4-byte
  `b <target>` thunks are almost all already correct.

### Repair a near miss instead of resampling it (`--repair`)

When a candidate already compiles to **exactly the original body length** and differs
in a few instructions, a retry is the wrong tool — the model found the shape; it needs
to be told which instructions are wrong. `--repair` seeds the loop from the entry's
**banked** candidate and asks for a *minimal edit* of that exact translation unit
(`tools/loop/repair.py`, wired in `run.process_repair`).

- **Eligibility is narrow.** Only a gate report with `status == "mismatch"`, compiled
  length == reference length, and ≤ `MAX_DIFF_WORDS` (6, i.e. 24 B) differing bytes. A
  `body-length` report is a *different shape*, not an edit — refused.
- **Monotone.** A reply replaces the best candidate only if `(|cand_len − ref_len|,
  diff_count)` strictly decreases (the bank's own `closeness`, from the gate report) —
  a repair session can never end worse than its seed.
- **The gate is still the only authority.** Every gated candidate is appended to the
  attempt log (`source: "repair"`, `repair_seed`) and folded into the bank; only the
  gate writes `verify=match`. Inline assembly is rejected *before* the gate, and a
  transport error removes the draft — `src/` stays matched-only.
- **`UNREACHABLE` is the honest exit.** If only register allocation differs, no source
  shape controls it — the model replies `UNREACHABLE` and the loop stops rather than
  burning rounds. Do not "fix" that with a barrier (banned, below).

`--repair` without `--entry` selects from the bank closest-first with the divergence
cap set to the repair budget; `--repair-rounds` (default 4) caps edits per entry. It is
a *conversion* mechanism for the near-miss band, not a substitute for a fresh pass.

### The inline-assembly rule (enforced)

Translated source must let the compiler choose every opcode: hand-written instructions
cannot match compiled C++. **One** `asm` spelling is allowed:

- a **symbol binding** attached to a declarator, `... f(void) asm("mangled.name");` —
  it emits nothing and only names the object symbol.

Everything else — `asm("nop")`, a top-level `asm("...")` statement, any instruction
string — is a violation. The loop **enforces** this (`run.asm_violation`): candidates
containing a disallowed construct are rejected before they reach the gate.

**The empty barrier is banned too** (`asm volatile("" ::: "memory")`), even though it
emits no instructions. It was previously allowed as a *scheduling* constraint, and
three tricks were built on it: the `guarded-word-index` template, a `bxCC lr`-guard
prompt section, and two hand-fixed functions. That was wrong in kind, not in degree:
the barrier only works because LLVM cannot predicate inline asm, so it coerces a branch
the reference compiler chose freely — the source no longer explains the bytes. All nine
dependent ledger rows were demoted to `verify=none`, and the template, the prompt
section, and the barrier allowance were removed (2026-11). Source that compiles only
because of an `asm` barrier is not a reconstruction; the honest result is
`verify=none` plus a near-miss note.

### Configuration search: exhausted — don't tune flags to fix residuals

A sweep of ~170 candidate profiles on 4.0.1 — scheduling (`-pre-RA-sched`,
`-misched*`, post-RA), if-conversion (`-disable-ifcvt-*`, `-ifcvt-limit`,
`-early-ifcvt-limit`, `-ifcvt-fn-*`), tail duplication/merging (`-disable-tail-duplicate`,
`-tail-dup-*`, `-tail-merge-*`), unrolling/inlining, GVN/LICM/CGP, register allocation,
the vectorisers, and `-O1/-Os/-Oz` — found **no profile better than
`-pre-RA-sched=source` alone (22 regressions)**:

- **6** (`6013fe3c` `604f8b78` `6050f78c` `6069d9e8` `6069ddfc` `6069eb18`) are fixed
  only by `-disable-ifcvt-simple`, which costs **156** regressions (it also breaks the
  common `if (c) return X;` guard);
- **2** (`6003bb78` `610b0960`) are fixed only by `-disable-ifcvt-simple-false`,
  which costs **92** (`610b0960` is also fixed by `-ifcvt-limit=0`);
- **2** (`6003bb78` `601cb7e8`) are fixed only by `-tail-merge-size<=1`, which costs
  **110** (90 new regressions);
- **13** are moved by **no knob at all**.

Note: `-mllvm -disable-ifcvt-simple` was previously fitted to the project's five PoC
fixtures (`find2`, `find3`, `find2s`, `findsub`, `new_a`) — loop-`return` shapes the
original did *not* if-convert — and it breaks the far more common `if (c) return X;`
guard (corpus dropped to 2,220/2,376, 93.4%, 156 regressions, 108 of them that guard).
The five PoC fixtures are a misleading sample; the four real probes (`613d733c`,
`60553a4c`, `60082510`, `6122c168`) are the honest evidence. `-hoist-cheap-insts=true`
is not needed on 4.0.1.

**Reference-project audit (2026-11) found nothing new.** SSBU (`-fno-common`,
`-fno-short-enums`, `-mno-implicit-float`, `-fno-strict-aliasing`,
`-fno-slp-vectorize`), OdysseyDecomp/Lego City (`-O3`, `-mno-implicit-float`,
`-fno-strict-aliasing`), sead (`-fno-strict-aliasing`), and forge's AArch32 Makefile
(`-march=armv8-a+crc+crypto`, `-mfpu=crypto-neon-fp-armv8`, `-mtune=cortex-a57`,
`-fno-threadsafe-statics`, `-fno-unwind-tables`) are all **inert** for this code
(identical objects) or change nothing on the 22; forge's `-mtp=soft` /
`-mfloat-abi=softfp` contradict the evidenced hardfp ABI. SSBU's `tools/fuzz_flags.py`
adds ~56 `-mllvm` candidates (machine sinking, block placement, live intervals,
scheduler); only three alter codegen and none fixes a residual. SSBU's remaining
leverage is non-stock — a patched compiler and object post-processing scripts — i.e. a
maintained fork or byte patching, not a stock configuration.

**`forge` is not a compiler option.** forge builds with devkitPro **devkitARM**
(`arm-none-eabi-g++`, GCC 13.2), not clang — a homebrew `subsdk` (libnx), not a
reconstruction of the game's executable. Measured directly: on 40 functions clang 4.0.1
matches, GCC reproduces **1/40** under both `-mfloat-abi=hard` and `softfp` (clang:
40/40). Its `-mtp=soft`, `-fpermissive`, `-enable-libstdcxx-allocator=new` are
GCC-only.

The residual is therefore not configuration-addressable: per-function
if-conversion/scheduling heuristic diffs vs the original's backend, or source-shape
issues. Fix these by re-deriving source shapes, not tuning flags.

### Pin-change gate: `tools/ledger/revalidate.py`

The gate for a pin change: selects every `verify=match` function, recompiles its
existing `src/` file with a chosen profile, re-runs the byte gate (faithfully resolving
the inventory body vs. the partition, and branch/pool relocations), and reports the
exact regressions. The default run loads `config/main/revalidate-known-residuals.tsv`,
which pins the 22 accepted clang 4.0.1 compiler residuals by address, gate status, and
divergence count (never by committed instruction bytes). Exact rows are reported as
`known-residual`; changed residuals, new regressions, resolved residuals, or missing
baseline entries all exit non-zero — so it can gate a pin flip in CI. Run with
`--clang PATH` to try an extracted tarball before the devcontainer is rebuilt.

> **Gate notes.**
> - The byte gate resolves branch/call and literal-pool relocations, so 4-byte
>   tail-call thunks (`b <target>`) now match; the raw-byte-gate era false-mismatched
>   every non-leaf. **Re-gate stored candidates before concluding a function is
>   unmatchable.**
> - **Extent rule:** every comparison needs an authoritative instruction-plus-pool
>   extent. `complexity.function_extent` derives it from the inventory instruction
>   bytes and their PC-relative literal-load targets, including alignment bytes. The
>   ledger partition and reference block are bounds only. Missing/invalid extents and
>   length mismatches fail closed; a candidate-sized matching prefix is never accepted.
> - **Read code with `clang -S` or Ghidra** — `llvm-objdump` 3.9.1 mis-decodes some
>   instructions and emits a byte-shifted stream.

### Tooling implications of the AArch32 target

- **open-ead/nx-decomp-tools is AArch64-only as-is** and cannot be adopted unchanged
  for a 32-bit ARM target. Evidence: `diff_settings.py` hardcodes `arch='aarch64'`;
  `viking/` uses `cs::arch::arm64::*` and matches `Arm64Insn` (incl. ADRP-based data
  tracking); `elf.rs` hardcodes 64-bit ELF + `R_AARCH64_*` relocations and `0x10`-byte
  PLT entries; `functions.rs` uses `ADDRESS_BASE=0x71_0000_0000`. Treat it as a
  **design reference** (function metadata + status tracking, relocation-aware reference
  checking, `check`/`listsym` tooling); a port or an `asm-differ`-based equivalent
  would be needed for AArch32.
- **Confirm ARM32 support** in `reccmp` / `asm-differ` / `splat` before committing to
  them for Phase 3.

---

## Validation

Every translated function must clear the gate; nothing else counts as done.

### Definition of "done" for a function

- [ ] Translated C++ compiles with the pinned toolchain.
- [ ] The diff tool reports a **byte-for-byte match** against the original.
- [ ] Data/BSS/address references are correctly relocated (passes the
      relocation/link check, not just the unlinked byte diff).

Byte-matching is the standard, but a small fraction of functions may only reach a
**behaviour** match (sm64ds/SSBU precedent). Those are tracked in the near-miss bank
and do not count as byte-matches.

---

## Workflow conventions (Phase 3)

- **Function splitting**: scripts isolate functions into individual compilation units
  so each can be matched independently.
- **Module isolation**: functions grouped into logical modules mirroring the original
  layout. The naming scheme is defined in [`docs/architecture.md`](docs/architecture.md)
  → *Symbol & data naming*.
- **Dual workflows, one gate**: manual or automated/LLM-assisted, every function passes
  the *same* byte-match gate. No source is trusted just because an AI produced it.
- **Near-miss bank**: an attempt that compiles to almost-right bytes is evidence, not
  waste. Record it (distance, what was tried) so it isn't redone.
- **Tests**: each tool's unit tests live under `tests/<tool>/` as plain `unittest`
  scripts — stdlib only, each runnable on its own while writing. Run the whole suite
  with `python3 tools/run_tests.py` (no pytest, no config).

---

## Commit & change hygiene

- Keep changes **surgical**: one function (or one logical module) per change when
  possible.
- Do not reformat or "improve" unrelated code.
- Prefer small diffs that are easy to byte-match-review.

---

## Repository hygiene (hard rules)

- **Never** add game data or anything derived from the original binary to the
  repository or a commit. Contributors supply their own copy locally under `baserom/`,
  which is git-ignored wholesale. This extends to issue/PR attachments and logs.
- This includes **decompiler/disassembler output**: Ghidra drafts (decompiled C),
  disassembly listings and memory-block dumps are generated into the git-ignored
  `baserom/work/` tree and are **never committed**. Only the reviewed, curated metadata
  they inform (e.g. the committed ledger) is committed — see
  [`docs/architecture.md`](docs/architecture.md).

---

## References for agents

Curated prior art (study for conventions; do not copy blindly):

- **MonsterDruide1/OdysseyDecomp** — closest Switch analog: devcontainer setup,
  per-function metadata, CMake+Ninja+ccache + clang/ld.lld, and the legal/dumping
  wording. Start here.
- **tangosdev/sm64ds-decomp** — automation-first: automatic templates, near-miss
  database, relocation-aware `linkcheck.py`, claims protocol. Borrow what fits the
  manual-first workflow.
- **Xeeynamo/sotn-decomp** — clean `tools/` layout, `Dockerfile`, uses `splat`,
  `asm-differ`, `decomp-permuter`, `decomp.me`, `frogress`.
- **pret** — `pokeemerald`/`pokefirered`: canonical matching-C structure and naming.
- **zeldaret** — `oot`/`mm`: mature matching-decomp structure and tooling.
- **Nintendocustom/Lego-City-Undercover-Decompilation** — third-party Switch C++
  matching decomp; the closest toolchain analog (clang 3.9.1, CMake+Ninja, musl
  sysroot, OdysseyDecomp-family `tools/`). Study its `tools/config.toml` +
  `ToolchainNX64.cmake`.
- **open-ead/sead** — first-party C++ stdlib decomp; source of the
  `MATCHING_HACK_NX_CLANG` precedent (upstream Clang matches Switch code).
- **sbergeron42/ssbu-decomp** — Smash Ultimate; documents which code resists stock
  Clang; source of `tools/fuzz_flags.py`.
- **open-ead/nx-decomp-tools** — Switch decomp tooling (AArch64-only; see caveat
  above).
- **Fexty12573/forge** — MHGU build/link mechanics and internal data-structure hints
  (GCC homebrew — **not** a compiler option for us).
- **reccmp** / **asm-differ** — the diff/matching tools.

---

## Open questions / TODO

- [x] **AArch32 vs AArch64** → **AArch32** (`ARM:LE:32:v8`, base `0x60000000`), via
      NPDM metadata and the Switch Loader's MOD0 heuristic.
- [x] **Compiler pin** → **clang 4.0.1 + `-mllvm -pre-RA-sched=source`**
      (`config/toolchain.json`), the only supported pin; the 5.0.1 + two-knob pin was
      retired (plan step 0.5). No stock configuration matches all seven probes —
      evidence for a non-stock/fork AArch32 backend; the real NintendoSDK toolchain is
      unobtainable, so 4.0.1 is the working pin and residual functions fall back to
      behaviour-match (sm64ds/SSBU precedent). Evidence:
      [`docs/compiler-identification.md`](docs/compiler-identification.md).
- [x] **Target title version** → **the latest title update** (CNMT `Patch`, version
      `262144`). Both builds report SDK `4.4.1` (compiler unchanged) and the aligned
      `.text` diff confirms an incremental patch, so no compiler reason to prefer base.
- [x] **Ghidra automation front-end** → **headless scripts**; GhidraMCP dropped. All
      Ghidra output is draft-only, generated into the git-ignored `baserom/work/`, and
      **never committed**; the committed ledger stays authoritative. See
      [`docs/architecture.md`](docs/architecture.md).
- [x] **Symbol/module naming convention** → `func_`/`D_`/`plt_` placeholders (full
      base), `g_`/`s_` scope prefixes, module namespaces for internal symbols,
      discovered mangling reproduced exactly for externals. See
      [`docs/architecture.md`](docs/architecture.md) → *Symbol & data naming*.
- [x] **Progress-tracking format** → **decomp.dev** (the objdiff `Report` v2 JSON),
      exported from the ledger by `tools/ledger/report.py`; published as a CI artifact
      named `<version>_report`. The site's decompiled figure maps to `verify=match`;
      its linked figure to the link build's verdict (`tools/build/linkcheck.py
      --report`, per-entry), falling back to `enroll=complete` when no link result is
      supplied — both via the shared predicate.
- [x] **Generated-vs-reviewed split** → **no folders**: it is ledger state, surfaced by
      tooling (see [`docs/architecture.md`](docs/architecture.md), *File layout &
      generated build*).
- [x] **Committed ledger schema + generator** → `config/main/ledger.tsv` (single
      module; content-only cut points + materialised `content` gaps + externals),
      produced by `tools/ledger/gen_ledger.py` from the inventory export as a frozen
      seed (refuses to overwrite barring `--force`; CI gated by
      `tools/ledger/validate.py`). `size` is the block *partition* (distance to the
      next cut point), not Ghidra's body span — see
      [`docs/architecture.md`](docs/architecture.md) → *Ledger — concrete schema*.
- [x] **Model C gate rig** → `tools/ledger/bytegate.py` (compile one function,
      byte-diff vs. the original), `tools/ledger/validate.py` (ledger invariants, the
      CI gate), `tools/ledger/ledgerlib.py` (schema + the one shared matched
      predicate), the reference cache `tools/ledger/refcache.py` (cached direct
      `.text` extraction keyed by NSO identity; `dump_blocks.sh` is the fallback for
      non-`.text` blocks and `refcache --check` verifies byte equivalence), and the
      compiler pin in `config/toolchain.json`.
- [ ] Verify ARM32 support in `reccmp` / `asm-differ` / `splat`; decide whether to port
      `nx-decomp-tools` or build on `asm-differ`.
- [ ] Decide how much of the sm64ds automation stack (templates, near-miss bank,
      claims protocol) to adopt for the manual-first workflow.

*(Expand this file as each item is resolved.)*
