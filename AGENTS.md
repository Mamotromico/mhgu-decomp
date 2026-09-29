# AGENTS.md

Guidance for coding agents (and any automated contributor) working on Soaratorium.

This file is a **living document** — it records conventions, pinned tooling, and
discoveries that agents must respect. Update it as the project learns things
(compiler version, symbol layout, naming rules, …). It complements
[README.md](README.md): the README is for humans, this file is the operational
contract for automated work.

---

## What this project is

A **decompilation** of *Monster Hunter Generations Ultimate* (Nintendo Switch). The
objective is a matching, buildable C++ source tree: functions translated from the
game's executable that compile to **byte-identical** machine code under the pinned
toolchain.

This is *not* a normal software project. The original binary is the single source of
truth, and every change to translated C++ must be validated against it (see
[Validation](#validation)).

---

## Core principles

1. **The binary is truth.** No "cleanup", refactor, or optimization is allowed if it
   breaks byte-matching. Readability is secondary to matching the compiler's output.
2. **Never invent behavior.** Every function must be traced back to the
   disassembly/decompiler output. Do not guess what a function "probably" does.
3. **One function at a time.** Small, verifiable units. Prefer matching a single
   function over touching many.
4. **Record findings.** When you discover something (compiler idiom, symbol naming,
   data layout), write it down here or in `docs/`.

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

The extracted executable is `baserom/main.nso` (git-ignored), a verified `NSO0` image:
SHA-256 `876b8587c37a7df77c40b4553dd5d7dcd0f2a898b84ca66f8ab863efbfd98b02`.

Loader-built memory map (base `0x60000000`):

| Block | Start | End |
| --- | --- | --- |
| `.text` | `0x60000000` | `0x613eec18` |
| `.rodata` | `0x613ef000` | `0x613ef068` |
| `.rodata.1` | `0x6154db25` | `0x6172758a` |
| `.data` | `0x61728000` | `0x61830e58` |
| `bss` | `0x61844000` | `0x6213f788` |

The loader also processes the ELF dynamic relocation metadata (`.rel.dyn` at
`0x13EF068`, `.rel.plt`, `.init_array`, and a constructed `got`), which is the basis
for the Phase 3 relocation/link check.

### Compiler & runtime (Phase 1 — partially resolved)

The **exact compiler version** determines whether byte-matching is possible and how
Phase 2 is pinned. Language and runtime are settled; the compiler version is not yet
pinned empirically:

```text
Architecture:  AArch32 (32-bit ARM) — confirmed, ARM:LE:32:v8, base 0x60000000
Language std:  C++17 (-std=c++1z) — confirmed (see below)
Runtime/libc:  NintendoSDK 4.4.x (nn:: C++ API), libc++ (-stdlib=libc++)
Compiler:      Clang-family, upstream — version NOT yet pinned.
               Leading candidate: clang 3.9.1 (inference, not yet proven)
```

**C++ is the target language.** Imports are the `nn::` C++ API in Itanium mangling, and
every Switch reference project is C++ (`sead`, BotW, SMO, SSBU, Lego City). Write `.cpp`
with C-style bodies; reach for C++ features (exceptions, templates, vtables) only where
the original forced them.

**Upstream Clang, not the proprietary NX fork.** Two *matching* Switch decomps build
against stock Clang from `releases.llvm.org`: `MonsterDruide1/OdysseyDecomp` (Super Mario
Odyssey) and `Nintendocustom/Lego-City-Undercover-Decompilation` (Lego City) both pin
**clang 3.9.1** under a `MATCHING_HACK_NX_CLANG` define. `open-ead/sead` (the first-party
C++ stdlib) also matches Switch code with upstream Clang. Only some SDK *internals* are
known to resist stock Clang (`sbergeron42/ssbu-decomp`).

**Candidate: clang 3.9.1.** SMO (2017) and Lego City Switch (2017) both resolved to it,
and MHGU ships the same NintendoSDK 4.4.x runtime. This is **inference, not proof** — pin
it by compiling a known leaf function with each candidate and byte-diffing (Phase 1
completion task). Full evidence and method:
[`docs/compiler-identification.md`](docs/compiler-identification.md).

> **SDK anchor:** `SdkAddon Ver.: 4.4.1 (v67371264)`, from the Program NCA header.

**Which title *version* to target is a separate open decision.** The Lego City decomp
deliberately targets its **v1.0.3 update** rather than the 1.0.0 releases — those "were
compiled with a different/unknown compiler version". So the matchable build is **not
always the earliest**. Two MHGU title versions are available locally (base `v0` and an
update build); compare them before committing.

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
- The cross-compiler is **deliberately absent** until Phase 1 identifies it. Do not
  add a guessed toolchain.

---

## Validation

Every translated function must clear the gate; nothing else counts as done.

### Definition of "done" for a function

- [ ] Translated C++ compiles with the pinned toolchain.
- [ ] The diff tool reports a **byte-for-byte match** against the original.
- [ ] Data/BSS/address references are correctly relocated (passes the
      relocation/link check, not just the unlinked byte diff).

---

## Workflow conventions (Phase 3)

- **Function splitting**: scripts isolate functions into individual compilation units
  so each can be matched independently.
- **Module isolation**: functions grouped into logical modules mirroring the original
  layout. Naming scheme TBD — keep names consistent with the disassembly.
- **Dual workflows, one gate**: manual or automated/LLM-assisted, every function
  passes the *same* byte-match gate. No source is trusted just because an AI produced
  it.
- **Near-miss bank**: an attempt that compiles to almost-right bytes is evidence, not
  waste. Record it (distance, what was tried) so it isn't redone.

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
      (`ARM:LE:32:v8`, base `0x60000000`), confirmed by the loader and NPDM alike.
- [ ] **Pin the compiler** (Phase 1 outcome). Settled: C++17, `nn::` runtime (SDK
      4.4.x). Candidate **clang 3.9.1** — confirm by byte-diffing a leaf function.
      Evidence in [`docs/compiler-identification.md`](docs/compiler-identification.md).
- [ ] **Choose the target title version** (base `v0` vs. the update build) — the
      matchable build is not always the earliest (Lego City precedent).
- [ ] Decide the Gold Ghidra automation front-end (headless scripts vs. GhidraMCP).
- [ ] Define the symbol/module naming convention.
- [ ] Verify ARM32 support in `reccmp` / `asm-differ` / `splat`; decide whether to port
      `nx-decomp-tools` or build on `asm-differ`.
- [ ] Choose the progress-tracking format (scoreboard / decomp.me / frogress).
- [ ] Decide how much of the sm64ds automation stack (templates, near-miss bank,
      claims protocol) to adopt for the manual-first workflow.

*(Expand this file as each item is resolved.)*
