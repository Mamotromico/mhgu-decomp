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
objective is a matching, buildable C source tree: functions translated from the
game's executable that compile to **byte-identical** machine code under the pinned
toolchain.

This is *not* a normal software project. The original binary is the single source of
truth, and every change to translated C must be validated against it (see
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

### Pinned versions — do not change without explicit approval

Byte-matching (and the prebuilt loader) depend on exact versions.

| Component | Pin | Notes |
| --- | --- | --- |
| Ghidra | `12.1.2` | **Not** 12.1.4 — the prebuilt loader is built against 12.1.2. |
| Ghidra SHA-256 | `b62e81a0390618466c019c60d8c2f796ced2509c4c1aea4a37644a77272cf99d` | Verified in the Dockerfile. |
| Ghidra Switch Loader | `1.6.1-c600d05-Ghidra_12.1.2` | Tag format `<ver>-<commit>-Ghidra_<ver>` — commit-specific, pin the full tag. |
| Loader SHA-256 | `0bc6374c11cb7a1275a0eda22184b9b2efe5a9a7e415cc29361c334966c1f477` | Verified in the Dockerfile. |
| Base image | `ubuntu:24.04` | Chosen for batteries-included apt; size is not a concern for a dev image. |

### Compiler identification (critical — do this before any translation)

The **exact compiler + SDK version** must be identified first; it determines whether
byte-matching is possible and how Phase 2 is pinned. Record it here when known:

```text
Architecture:  [TODO — likely AArch32 (32-bit ARM); see lead below]
Compiler:      [TODO — e.g. ARM32 Clang x.y.z / Nintendo SDK version]
Language std:  [TODO — e.g. C++17 / C11]
Runtime/libc:  [TODO — e.g. SDK libc, allocator]
```

> **Lead (unverified):** [`Fexty12573/forge`](https://github.com/Fexty12573/forge)
> builds against devkitPro/devkitARM + `libnx` + `skyline` and uses a `switch32.ld`
> linker script — implying the executable is **AArch32**, not AArch64. Verify against
> the real binary before pinning the toolchain; do **not** assume the AArch64 SDK
> default.

### Tooling implications of a possible AArch32 target

- **open-ead/nx-decomp-tools is AArch64-only as-is** and cannot be adopted unchanged
  if the target is 32-bit ARM. Evidence: `diff_settings.py` hardcodes
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

- [ ] Translated C compiles with the pinned toolchain.
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
- **open-ead/nx-decomp-tools** — Switch decomp tooling (see AArch32 caveat above).
- **Fexty12573/forge** — MHGU build/link mechanics and internal data-structure hints.
- **reccmp** / **asm-differ** — the diff/matching tools.

---

## Open questions / TODO

- [ ] Load the executable in Ghidra; confirm **AArch32 vs AArch64**.
- [ ] Identify the **compiler/SDK version** (Phase 1 outcome) and pin it in Phase 2.
- [ ] Decide the Gold Ghidra automation front-end (headless scripts vs. GhidraMCP).
- [ ] Define the symbol/module naming convention.
- [ ] Verify ARM32 support in `reccmp` / `asm-differ` / `splat`; decide whether to port
      `nx-decomp-tools` or build on `asm-differ`.
- [ ] Choose the progress-tracking format (scoreboard / decomp.me / frogress).
- [ ] Decide how much of the sm64ds automation stack (templates, near-miss bank,
      claims protocol) to adopt for the manual-first workflow.

*(Expand this file as each item is resolved.)*
