# AGENTS.md

Guidance for coding agents (and any automated contributor) working on mhgu-decomp.

This file is a **living document** — it records conventions, pinned tooling, and
discoveries that agents must respect. Update it as the project learns things
(compiler version, symbol layout, naming rules, …). It complements
[README.md](README.md): the README is for humans, this file is the operational
contract for automated work.

---

## What this project is

A **decompilation** of *Monster Hunter Generations Ultimate* (Nintendo Switch). The
objective is a **clean-room reconstruction**: a matching, buildable C++ source tree whose
functions, translated from the game's executable, compile to **byte-identical** machine
code under the pinned toolchain (or as close as that toolchain allows).

This is *not* a normal software project. The original binary is the single source of
truth, and every change to translated C++ must be validated against it (see
[Validation](#validation)).

---

## Core principles

1. **The binary is truth.** No "cleanup", refactor, or optimization is allowed if it
   breaks byte-matching.
2. **Never invent behavior.** Every function must be traced back to the
   disassembly/decompiler output. Do not guess what a function "probably" does.
3. **One function at a time.** Small, verifiable units. Prefer matching a single
   function over touching many.
4. **Record findings.** When you discover something (compiler idiom, symbol naming,
   data layout), write it down here or in `docs/`.
5. **Byte-match first, readability second.** Byte-matching is the standard, but the
   project is realistic: some functions may only reach a *behaviour* match. Readability
   is a deliberate second goal (this is a learning project too) and becomes the focus
   once most functions match (target: ~90%). Output from automated tooling that
   optimises only for a byte match is allowed to be unreadable, but must stay
   distinguishable from human-reviewed, readability-improved code (see
   [Generated vs. reviewed code](#generated-vs-reviewed-code)).

## README is human-facing — flag agent edits

`README.md` is the introduction and instructions for human developers, so it should be
written (or at least thoroughly reviewed) by a person. Any content an agent/LLM writes or
rewrites in `README.md` must be wrapped in the review markers `>🤖` (open) and `🤖<`
(close) until a human reviews and adopts it, at which point the markers are removed. The
markers mean "agent-authored, not yet human-reviewed". Pure removals need no marker — they
show up in the diff.

## Generated vs. reviewed code

Two tiers of translated output exist and must not be confused:

- **Generated (byte-match-first).** Produced by automated / LLM-assisted tooling whose
  only requirement is a byte match. It may be unreadable; that is acceptable.
- **Reviewed (readability-improved).** A human has reworked generated code to make it
  understandable *while preserving the byte match*.

The tiers must be **distinguishable** so a reader never mistakes generated code for
deliberately-written code. **Decided:** the distinction is **ledger state, not a folder
layout** — a folder-per-state split was considered and rejected (one folder expresses one
axis, per file only, and a merged translation unit has mixed state). The tier is recorded on
the ledger entry and surfaced by tooling; files are kept primarily one function per file and
merged only when the original grouping is required for codegen. See
[`docs/architecture.md`](docs/architecture.md) → *File layout & generated build*.

---

## Analysis environment (Phase 1)

Ghidra and its Switch loader live **inside the devcontainer**, so no host Java is
required. Build/run details are in the [README](README.md); the facts an agent needs:

- **Ghidra 12.1.2** at `/opt/ghidra` (`GHIDRA_HOME`).
- **Java 21 JDK** at `JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64`.
- **Ghidra Switch Loader** extension under `${GHIDRA_HOME}/Ghidra/Extensions/SwitchLoader`.
- Wrappers: `.devcontainer/scripts/ghidra-headless.sh` (automation) and
  `ghidra-gui.sh` (GUI via noVNC/X11).

> **Ghidra project location:** keep the project under `baserom/ghidra/` — it embeds
> bytes derived from the original binary, and `baserom/*` is git-ignored wholesale.
> Analysts run the headless import (import-only, `-noanalysis`) against
> `baserom/main.nso`; the resulting log belongs under `baserom/work/`.

### Pinned versions — do not change without explicit approval

Byte-matching (and the prebuilt loader) depend on exact versions.

| Component | Pin | Notes |
| --- | --- | --- |
| Ghidra | `12.1.2` | **Not** 12.1.4 — the prebuilt loader is built against 12.1.2. |
| Ghidra SHA-256 | `b62e81a0390618466c019c60d8c2f796ced2509c4c1aea4a37644a77272cf99d` | Verified in the Dockerfile. |
| Ghidra Switch Loader | `1.6.1-c600d05-Ghidra_12.1.2` | Tag format `<ver>-<commit>-Ghidra_<ver>` — commit-specific, pin the full tag. |
| Loader SHA-256 | `0bc6374c11cb7a1275a0eda22184b9b2efe5a9a7e415cc29361c334966c1f477` | Verified in the Dockerfile. |
| clang | `4.0.1` | The compiler pin (reproduction stand-in); installed at `/opt/clang-4.0.1`, on `PATH`. |
| clang tarball SHA-256 | `ca48a4def4cbc9dd6af3f46ce1dc2bd903d26c7ad51387f57884ad1eaa58e42f` | Verified in the Dockerfile. |
| clang (secondary) | `5.0.1` | Kept at `/opt/clang-5.0.1` (not on `PATH`) for A/B runs and the few 5.0.1-only functions; `config/toolchain-5.0.1.json`. |
| libtinfo5 | `6.1-1ubuntu1.18.04.1` | ncurses-5 ABI the pinned clang links against; from the Ubuntu 18.04 archive. |
| Base image | `ubuntu:24.04` | Chosen for batteries-included apt; size is not a concern for a dev image. |

### Architecture (confirmed)

The target is **AArch32 (32-bit ARM)**, not the more common AArch64 Switch target.
Two independent sources agree:

- **NPDM metadata** (`main.npdm`, from the ExeFS): `Is64BitInstruction: false` and
  `ProcessAddressSpace: AddressSpace32BitNoReserved`.
- **Ghidra Switch Loader**, on import of `baserom/main.nso`: selected
  `Using Language/Compiler: ARM:LE:32:v8:default` via its MOD0 dynamic-table heuristic
  (`NXOAdapter.isAarch32()`). Image base is `0x60000000`.

This corroborates the [`Fexty12573/forge`](https://github.com/Fexty12573/forge) lead
(devkitPro/devkitARM + `switch32.ld`). Do **not** assume the AArch64 SDK default.

The extracted executable is `baserom/main.nso` (git-ignored), a verified `NSO0` image —
the **latest title update** (`b3935415…645ef`). See the target-version note below.

Loader-built memory map (base `0x60000000`):

| Block | Start | End |
| --- | --- | --- |
| `.text` | `0x60000000` | `0x613f1dec` |
| `.rodata` | `0x613f2000` | `0x613f206c` |
| `.rodata.1` | `0x61550ccb` | `0x6172e6fa` |
| `.data` | `0x6172f000` | `0x61837f28` |
| `bss` | `0x6184b000` | `0x62146788` |

The loader also processes the ELF dynamic relocation metadata (`.rel.dyn` at
`0x13F206C`, `.rel.plt`, `.init_array`, and a constructed `got` from `0x1838AE8` to
`0x1848900`), which is the basis for the Phase 3 relocation/link check.

### Compiler & runtime (Phase 1 — resolved, de facto pin)

The toolchain is settled to a **de facto pin**, not the vendor's true toolchain (that is a
NintendoSDK build and is not obtainable):

```text
Architecture:  AArch32 (32-bit ARM) — confirmed, ARM:LE:32:v8, base 0x60000000
Language std:  C++17 (-std=c++1z) — confirmed (see below)
Runtime/libc:  NintendoSDK 4.4.x (nn:: C++ API), libc++ (-stdlib=libc++)
Compiler:      clang 5.0.1 — DE FACTO pin (reproduction stand-in) + two hidden
               backend flags; no stock configuration matches all probes (best 6/7)
Float:         ARMv8-A FP + NEON (Cortex-A57 feature set) — hardfp ABI
```

**Build flags (the de facto pin):**

```text
clang -target armv8a-none-eabi -mfpu=neon-fp-armv8 -mfloat-abi=hard \
      -O2 -fomit-frame-pointer -fPIC -fno-exceptions -fno-rtti \
      -ffreestanding -std=c++1z \
      -mllvm -pre-RA-sched=source -mllvm -hoist-cheap-insts=true
```

**C++ is the target language.** Imports are the `nn::` C++ API in Itanium mangling, and
every Switch reference project is C++ (`sead`, BotW, SMO, SSBU, Lego City). Write `.cpp`
with C-style bodies; reach for C++ features (exceptions, templates, vtables) only where
the original forced them.

**Upstream Clang, not the proprietary NX fork.** Two *matching* Switch decomps build
against stock Clang from `releases.llvm.org` (`OdysseyDecomp` and
`Lego-City-Undercover-Decompilation`, both clang 3.9.1); `open-ead/sead` also matches with
upstream Clang. Only some SDK *internals* are known to resist stock Clang
(`sbergeron42/ssbu-decomp`).

**Compiler: clang 5.0.1 — de facto pin.** Six of the seven reconstructed probes byte-match
under **5.0.1 with no `-mcpu`**, the ARMv8-A FP/NEON feature set, and two hidden backend
flags; the seventh (the 28-byte struct copy) is a known residual. **No stock config matches
all seven** — the best stock configuration reaches 6/7. The residual gap is two independent
backend heuristics:

- `find_entry`'s `uxtb` **hoisting** — the `MachineLICM` cheap-instruction register-pressure
  gate → `-mllvm -hoist-cheap-insts=true`.
- `new_b`'s loop-body **ordering** — the SelectionDAG (ISel) list scheduler's latency model
  → `-mllvm -pre-RA-sched=source` (the divergence is already present at
  `Before Expand ISel Pseudo-instructions`, not in the MachineScheduler).

A stock compiler that differs from *every* stock configuration in **two** separate
scheduling heuristics is positive evidence for a **non-stock/fork AArch32 backend** (the
SSBU precedent). Both `-mllvm` flags are **hidden diagnostics, not real build settings**;
they make our build emit what the original emitted. Because the real NintendoSDK toolchain
is unobtainable, the project adopts **5.0.1 + both knobs** as a **de facto pin** until
proven otherwise.

**No `-mcpu`.** `-mcpu=cortex-a57` was copied from the AArch64 reference projects and is
**wrong** for this 32-bit target. `-mtune` is inert in clang 5.0.1's ARM32 backend. Target
SoC is the **Tegra X1 (T210, "Erista")** (`4×Cortex-A57 + 4×Cortex-A53`; A57 cluster only).
Dropping `-mcpu` alone raises 5.0.x from 3/5 to 4/5 on the original corpus.

**ARMv8-A FP + NEON (corrected).** The pin is `-mfpu=neon-fp-armv8` (the Cortex-A57 AArch32
feature set), **not** `-mfpu=vfpv4-d16`. The original `.text` provably contains instructions
VFPv4 cannot emit: ARMv8-A FP (`vseleq/vselgt/vselge`, `vmaxnm/vminnm`, `vrintm/vrinta`,
`vcvtp` — `0xFE…`, ~2,946 words) in ~1,041 functions, and NEON (`vmax/vmin/vdup/vld1`,
`0xF2`–`0xF7`) in ~318 functions — ~1,259 functions (2.93%) that a VFP-only build can never
match. The earlier "VFP-only, NEON off" conclusion came from counting only `0xEE`/`0xED`
(missing `0xFE` and `0xF2`–`0xF7`) and from the one probe whose source hits clang's NEON
block-copy lowering; it was never exercised on this code because all matched functions were
trivial leaves (median body 8 B — selection bias). Recompiling the 7 probes with
`neon-fp-armv8` leaves **6/7 instruction-identical**; only the struct-copy probe changes
(clang emits NEON `vld1/vst1` for 16-byte block copies, the original uses integer `ldm/stm`
— a backend residual, not a source-shape issue). `-O2`/`-O3` remain indistinguishable. Float
arguments/results still cross the ABI in the VFP s-registers (**hardfp**,
`-mfloat-abi=hard`). Full evidence and method:
[`docs/compiler-identification.md`](docs/compiler-identification.md).

### Compiler pin revision: clang 4.0.1 + `-pre-RA-sched=source` (evidence)

The 5.0.1 pin cannot reproduce some instruction-selection and scheduling choices the
original made, so a large class of functions is **structurally unmatchable** under it
(no C source shape and no `-mllvm` knob fixes them — verified by exhaustive flag
search). The divergence classes:

- **`bfc` vs `bic`.** For a bitfield clear whose mask is BIC-encodable (e.g. `x & ~3`),
  clang 5.0.1 always emits `bic`; the original emits `bfc`. 4,173 ledger functions
  contain a true `bfc` (R15 base); 3,379 of them have only BIC-encodable clear masks and
  **none** have ever matched under 5.0.1.
- **If-conversion.** For a small `if` with a store, the original predicates the body
  (`movweq`/`strbeq`); 5.0.1 emits an early-return branch.
- **Scheduling.** e.g. the original loads both operands before zeroing the result
  register; 5.0.1 interleaves the zeroing.

**clang 4.0.1** reproduces all three exactly. Under 4.0.1 it:

- matches the four representative probes 5.0.1 fails (`613d733c`, `60553a4c`,
  `60082510`, `6122c168`) — these are real game functions, and they match **without**
  any if-conversion knob;
- matches **2,354 / 2,376** of the already-matched `src/` corpus (**99.1%**, after the
  source re-derivation described below);
- re-gates **10/23** stored `deepseek-v4-pro` candidates from mismatch to match.

**The profile carries only `-mllvm -pre-RA-sched=source`.** It fixes three corpus
regressions and breaks none. The earlier candidate, `-mllvm -disable-ifcvt-simple`,
was **wrong**: it was fitted to the project's own five PoC fixtures (`find2`, `find3`,
`find2s`, `findsub`, `new_a`), which are loop-`return` shapes the original did *not*
if-convert, but it breaks the far more common `if (c) return X;` guard (4.0.1's default
predicates that exactly the way the original does) — re-gating the whole corpus under
it dropped to **2,220 / 2,376 (93.4%)**, 156 regressions, 108 of them that guard. The
five PoC fixtures are therefore a misleading sample; the four real probes are the
honest evidence. `-hoist-cheap-insts=true` is not needed on 4.0.1.

The profile is `config/toolchain.json` (the default); 5.0.1 remains selectable via
`config/toolchain-5.0.1.json`. The Dockerfile installs 4.0.1 to `/opt/clang-4.0.1` on
`PATH`, with 5.0.1 kept alongside at `/opt/clang-5.0.1`.

**Status: now the default.** 4.0.1 is the pin (the devcontainer ships `/opt/clang-4.0.1`).
Source shapes were re-derived under 4.0.1, taking the corpus from 27 to **22 remaining
regressions**
(10 `body-length`, 12 `mismatch`):

- **predicated early return in a loop** (7: `6013fe3c`, `604f8b78`, `6050f78c`,
  `6069d9e8`, `6069ddfc`, `6069eb18`, `610b0960`) — 4.0.1 if-converts a loop-exit
  `return` into `popcc {…,pc}`; the original branches. No source shape (early return,
  ternary, `break`+result, nested if, `__builtin_expect`, inline-asm barrier) defeats
  it; only disabling the if-converter globally does, at the cost of the 108 guards
  above. Note the reference *does* if-convert leaf `return` guards (`bxne lr`), so this
  is a `pop {…,pc}`-specific heuristic difference. **Accepted residual.**
- **instruction ordering** (5: `602aa498`, `602aa814`, `6050c964`, `60876a94`,
  `610e897c`) — two independent loads/ops swapped. Statement reordering does not change
  SelectionDAG scheduling; no `-pre-RA-sched`/`-misched`/`-regalloc` knob matches it.
  An `asm volatile("" ::: "memory")` barrier fixes three of the original eight (see
  below) but not these. **Accepted residual.**
- **multi-instruction predicated return** (5: `605bc604`, `60627aac`, `61122598`,
  `613720ec`, `605089e4`) — the original predicates `ldrbne/movne/cmpne/bxne lr`;
  4.0.1 branches (or predicates the other side). **Accepted residual.**
- **tail-duplication / block placement** (2: `6003bb78` — one branch byte only,
  `601cb7e8`) and **stack-argument hoisting** (2: `601ac4d8`, `60c17abc`) — 4.0.1 hoists
  the 5th-argument load above the first store, and duplications differ. `-disable-tail-
  duplicate` fixes these but drops the corpus to 2,290, so it cannot be global.
  **Accepted residual.**
- **4.0.1-vs-5.0.1 DAG choice** (1: `60260440` — predicates the else-body instead of the
  hoisted `mov`+`bxhi lr`). **Accepted residual.**

Eight were fixed by re-deriving the source shape under 4.0.1 (all still byte-match):
`func_6018e958` (early-return form gives `movne` instead of `movwne`),
`func_6054ee64` (store the halfword before loading the divisor), `func_6003b788`
(nested `if` instead of `continue`), `func_6080c93c` (`unsigned char x = field; x--;`
instead of `(unsigned char)(field - 1)`, which defeats the mask DAG-combine),
`func_6016b920` (the same in-place `unsigned short` increment trick),
`func_6053a058` and `func_6018b110` (an `asm volatile("" ::: "memory")` barrier
between the argument loads and the callee-pointer load pins the reference order), and
`func_600a7e80` (a 4-byte `bx lr` stub; the ledger claimed `verify=match` with no
source).

**Configuration search: exhausted.** A sweep of ~170 candidate profiles on 4.0.1 —
scheduling (`-pre-RA-sched`, `-misched*`, post-RA), if-conversion
(`-disable-ifcvt-*`, `-ifcvt-limit`, `-early-ifcvt-limit`, `-ifcvt-fn-*`), tail
duplication/merging (`-disable-tail-duplicate`, `-tail-dup-size/-limit/-placement-*`,
`-tail-merge-*`), unrolling/inlining, GVN/LICM/CGP, register allocation, the
vectorisers, and `-O1/-Os/-Oz` — found **no profile better than
`-pre-RA-sched=source` alone (22 regressions)**. The residual splits as:

- **6** (`6013fe3c`, `604f8b78`, `6050f78c`, `6069d9e8`, `6069ddfc`, `6069eb18`)
  are fixed only by `-disable-ifcvt-simple`, which costs **156** regressions (it also
  breaks the common `if (c) return X;` guard);
- **2** (`6003bb78`, `610b0960`) are fixed only by `-disable-ifcvt-simple-false`,
  which costs **92** (`610b0960` is also fixed by `-ifcvt-limit=0`);
- **2** (`6003bb78`, `601cb7e8`) are fixed only by `-tail-merge-size<=1`, which costs
  **110** (90 new regressions);
- **13** are moved by **no knob at all**.

**Reference-project audit (2026-11) found nothing new.** Cross-checked the real
Switch decomp toolchains: SSBU (`-fno-common`, `-fno-short-enums`,
`-mno-implicit-float`, `-fno-strict-aliasing`, `-fno-slp-vectorize`),
OdysseyDecomp/Lego City (`-O3`, `-mno-implicit-float`, `-fno-strict-aliasing`),
sead (`-fno-strict-aliasing`), and MHGU's own `forge` AArch32 Makefile
(`-march=armv8-a+crc+crypto`, `-mfpu=crypto-neon-fp-armv8`, `-mtune=cortex-a57`,
`-fno-threadsafe-statics`, `-fno-unwind-tables`). All are **inert** for this code
(identical objects) or change nothing on the 22; forge's `-mtp=soft` /
`-mfloat-abi=softfp` are GCC/ABI choices incompatible with the evidenced hardfp
clang pin. SSBU's `tools/fuzz_flags.py` adds ~56 `-mllvm` candidates (machine
sinking, block placement, live intervals, scheduler); only three alter codegen
(`-disable-machine-sink`, `-join-liveintervals=false`, `-machine-sink-split=false`)
and none fixes a residual. SSBU's remaining leverage is non-stock: a patched
compiler (`-mllvm -aarch64-nx-prologue`, +91 matches) and object post-processing
scripts (`fix_prologue_sched`, `fix_insn_reorder`, `fix_return_width`, …) — i.e.
a maintained fork or byte patching, not a stock configuration.

**`forge` is not a compiler option.** forge builds with devkitPro **devkitARM**
(`arm-none-eabi-g++`, GCC 13.2), not clang — it is a homebrew `subsdk` (libnx),
not a reconstruction of the game's executable. Measured directly: on 40
functions that clang 4.0.1 already matches, GCC reproduces **1/40** under both
`-mfloat-abi=hard` and `softfp` (clang: 40/40). Its `-mtp=soft`,
`-fpermissive`, `-enable-libstdcxx-allocator=new` are GCC-only, and its `softfp`
ABI contradicts the game's evidenced hardfp float passing.

The residual is therefore not configuration-addressable: it is a per-function
if-conversion/scheduling heuristic difference between 4.0.1 and the original's
backend, or a source-shape issue. Fixing these means re-deriving source shapes, not
tuning flags.

`tools/ledger/revalidate.py` is the gate for a pin change: it selects every
`verify=match` function, recompiles its existing `src/` file with a chosen profile,
re-runs the byte gate (faithfully resolving the inventory body vs. the partition, and
branch/pool relocations), and reports the exact regressions. It writes JSON/TSV
reports and exits non-zero when anything regresses, so it can gate a pin flip in CI.
Run it with `--clang PATH` to try an extracted tarball before the devcontainer is
rebuilt.

> **Note (gate):** the byte gate already resolves branch/call and literal-pool
> relocations, so 4-byte tail-call thunks (`b <target>`) now match; earlier runs that
> used a raw-byte gate produced false mismatches on every non-leaf. Re-gate stored
> candidates before concluding a function is unmatchable.

> **Running clang:** the devcontainer ships the pinned compiler at `/opt/clang-4.0.1`
> (on `PATH`, so `clang`/`clang++` resolve to it) with the `libtinfo.so.5` it needs;
> `/opt/clang-5.0.1` is kept as a secondary (see `config/toolchain-5.0.1.json`).
> Note `llvm-objdump` 3.9.1 mis-decodes some instructions and emits a byte-shifted
> stream: **read code with `clang -S` or Ghidra.**

> **SDK anchor:** `SdkAddon Ver.: 4.4.1 (v67371264)`, from the Program NCA header.

**Target version: the latest title update (resolved).** We target the update build rather
than base `v0`: both report the identical `SdkAddon Ver.: 4.4.1 (v67371264)`, and an
aligned `.text` diff shows the update is an incremental patch over an otherwise-identical
codebase (≈81% byte overlap), so the compiler gives no reason to prefer base. Locally
`baserom/main.nso` **is the update** (`b3935415…`). See
[`docs/compiler-identification.md`](docs/compiler-identification.md).

### Tooling implications of the AArch32 target

- **open-ead/nx-decomp-tools is AArch64-only as-is** and cannot be adopted unchanged
  for a 32-bit ARM target. Evidence: `diff_settings.py` hardcodes
  `arch='aarch64'`; `viking/` uses `cs::arch::arm64::*` and matches `Arm64Insn`
  (incl. ADRP-based data tracking); `elf.rs` hardcodes 64-bit ELF + `R_AARCH64_*`
  relocations and `0x10`-byte PLT entries; `functions.rs` uses
  `ADDRESS_BASE=0x71_0000_0000`. Treat it as a **design reference** (function
  metadata + status tracking, relocation-aware reference checking, `check`/`listsym`
  tooling); a port or an `asm-differ`-based equivalent would be needed for AArch32.
- **Confirm ARM32 support** in `reccmp` / `asm-differ` / `splat` before committing to
  them for Phase 3.

---

## Build environment (Phase 2)

- Reproducible via the **devcontainer / Dockerfile**; the container is the source of
  truth for the toolchain.
- The compiler/SDK is **pinned** — do not "upgrade" tooling without explicit
  approval; byte-matching depends on exact versions.
- The **compiler is installed**: the Dockerfile downloads the pinned clang 4.0.1
  tarball (SHA-256 verified) to `/opt/clang-4.0.1` on `PATH`, with the `libtinfo5` it
  needs (5.0.1 is kept at `/opt/clang-5.0.1` as a secondary). It ships the *bare*
  compiler; the project's target flags are applied by the
  build (see [Compiler & runtime](#compiler--runtime-phase-1--resolved-de-facto-pin)).
  Do not add a guessed toolchain or a third clang.

---

## Validation

Every translated function must clear the gate; nothing else counts as done.

### Definition of "done" for a function

- [ ] Translated C++ compiles with the pinned toolchain.
- [ ] The diff tool reports a **byte-for-byte match** against the original.
- [ ] Data/BSS/address references are correctly relocated (passes the
      relocation/link check, not just the unlinked byte diff).

Byte-matching is the standard, but it's possible that a small fraction of
functions may only reach a **behaviour** match (sm64ds/SSBU precedent). Those are tracked
in the near-miss bank and do not count as byte-matches.

---

## Workflow conventions (Phase 3)

- **Function splitting**: scripts isolate functions into individual compilation units
  so each can be matched independently.
- **Module isolation**: functions grouped into logical modules mirroring the original
  layout. The naming scheme is defined in [`docs/architecture.md`](docs/architecture.md) →
  *Symbol & data naming*.
- **Dual workflows, one gate**: manual or automated/LLM-assisted, every function
  passes the *same* byte-match gate. No source is trusted just because an AI produced
  it.
- **Near-miss bank**: an attempt that compiles to almost-right bytes is evidence, not
  waste. Record it (distance, what was tried) so it isn't redone.
- **Tests**: each tool's unit tests live under `tests/<tool>/` as plain `unittest`
  scripts — stdlib only, each runnable on its own while writing. Run the whole suite with
  `python3 tools/run_tests.py` (no pytest, no config).

---

## Commit & change hygiene

- Keep changes **surgical**: one function (or one logical module) per change when
  possible.
- Do not reformat or "improve" unrelated code.
- Prefer small diffs that are easy to byte-match-review.

---

## Repository hygiene (hard rules)

- **Never** add game data or anything derived from the original binary to the
  repository or a commit. Contributors supply their own copy locally under
  `baserom/`, which is git-ignored wholesale. This extends to issue/PR attachments
  and logs.
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
  matching decomp; the closest toolchain analog (clang 3.9.1, CMake+Ninja, musl sysroot,
  OdysseyDecomp-family `tools/`). Study its `tools/config.toml` + `ToolchainNX64.cmake`.
- **open-ead/sead** — first-party C++ stdlib decomp; source of the
  `MATCHING_HACK_NX_CLANG` precedent (upstream Clang matches Switch code).
- **sbergeron42/ssbu-decomp** — Smash Ultimate; documents which code resists stock
  Clang (some SDK internals are not matchable with upstream Clang).
- **open-ead/nx-decomp-tools** — Switch decomp tooling (see AArch32 caveat above).
- **Fexty12573/forge** — MHGU build/link mechanics and internal data-structure hints.
- **reccmp** / **asm-differ** — the diff/matching tools.

---

## Open questions / TODO

- [x] Load the executable in Ghidra; confirm **AArch32 vs AArch64** → **AArch32**
      (`ARM:LE:32:v8`, base `0x60000000`), confirclang 5.0.1 + two hidden backend
      flags** was the initial de facto pin; it was **revised to clang 4.0.1 +
      `-mllvm -pre-RA-sched=source`** (see "Compiler pin revision" above), which is now
      the project default (`config/toolchain.json`). All seven probe functions byte-match
      under it; **no stock configuration** does (best 5/7). The residual gap is two
      independent backend heuristics, positive evidence for a **non-stock/fork AArch32
      backend**; since the real NintendoSDK toolchain is unobtainable, 4.0.1 is adopted
      as the working pin. Residual functions fall back to behaviour-match (sm64ds/SSBU
      precedent). Residual functions fall back to behaviour-match (sm64ds/SSBU precedent).
      Evidence in [`docs/compiler-identification.md`](docs/compiler-identification.md).
- [x] **Choose the target title version** → **the latest title update** (CNMT `Patch`,
      version `262144`). Both builds report SDK `4.4.1` (compiler unchanged) and the
      aligned `.text` diff confirms an incremental patch, so the compiler gives no reason to prefer base.
      Evidence: [`docs/compiler-identification.md`](docs/compiler-identification.md).
- [x] **Decide the Gold Ghidra automation front-end** → **headless scripts**; GhidraMCP
      dropped. All Ghidra output is draft-only, generated into the git-ignored
      `baserom/work/`, and **never committed**; the committed ledger stays authoritative.
      See [`docs/architecture.md`](docs/architecture.md).
- [x] Define the symbol/module naming convention → `func_`/`D_` placeholders (full base),
      `g_`/`s_` scope prefixes, module namespaces for internal symbols, discovered mangling
      reproduced exactly for externals. See [`docs/architecture.md`](docs/architecture.md) →
      *Symbol & data naming*.
- [ ] Verify ARM32 support in `reccmp` / `asm-differ` / `splat`; decide whether to port
      `nx-decomp-tools` or build on `asm-differ`.
- [x] Choose the progress-tracking format → **decomp.dev** (the objdiff `Report` v2 JSON),
      exported from the ledger by `tools/ledger/report.py`; published as a CI artifact named
      `<version>_report`. The site's decompiled figure maps to `verify=match`; its linked figure
      to the link build's verdict (`tools/build/linkcheck.py --report`, per-entry), falling back
      to `enroll=complete` when no link result is supplied — both via the shared predicate.
- [ ] Decide how much of the sm64ds automation stack (templates, near-miss bank,
      claims protocol) to adopt for the manual-first workflow.
- [x] Decide the generated-vs-reviewed split (separate folders + review tooling?) →
      **no folders**: it is ledger state, surfaced by tooling (see
      [`docs/architecture.md`](docs/architecture.md), *File layout & generated build*).
- [x] Define the committed ledger schema + generator → `config/main/ledger.tsv` (single module;
      content-only cut points + materialised `content` gaps + externals), produced by
      `tools/ledger/gen_ledger.py` from the inventory export as a frozen seed (CI gated
      by `tools/ledger/validate.py`). `size`
      is the block *partition* (distance to the next cut point), not Ghidra's body span — see
      [`docs/architecture.md`](docs/architecture.md) → *Ledger — concrete schema*.
- [x] Build the Model C gate rig → `tools/ledger/bytegate.py` (compile one function, byte-diff
      vs. the original), `tools/ledger/validate.py` (ledger invariants, the CI gate),
      `tools/ledger/ledgerlib.py` (schema + the one shared matched predicate), reference bytes
      from `tools/ghidra/dump_blocks.sh`, and the compiler pin in `config/toolchain.json`. The
      ledger is a **frozen seed** (`gen_ledger.py` refuses to overwrite barring `--force`).

*(Expand this file as each item is resolved.)*
