# Compiler & runtime identification (Phase 1)

How the toolchain behind `baserom/main.nso` was identified, and the working result. The
binary is truth; treat everything here as evidence toward the *working* pin, not a claim
about the vendor's true toolchain (a NintendoSDK build, and not obtainable).

## Settled

| Question | Answer | Evidence |
| --- | --- | --- |
| Architecture | AArch32 (`ARM:LE:32:v8`), base `0x60000000` | Ghidra loader + NPDM metadata |
| Language | **C++17** | `nn::` API imports in Itanium mangling; all Switch reference projects are C++ |
| Runtime | NintendoSDK 4.4.x (`nn::`), libc++ | NCA header `SdkAddon Ver. 4.4.1`; import names |
| Target SoC | Tegra X1 (T210, "Erista"), `4×Cortex-A57 + 4×Cortex-A53`; **A57 cluster only** | Wikipedia *Tegra* (Switch `ODNX02-A2`) |
| Float | ARMv8-A FP + NEON (Cortex-A57 feature set); **hardfp** ABI (`-mfloat-abi=hard`) | A2/A3, A4, *Correction* |

## Compiler — de facto pin: clang 5.0.1 + two backend knobs

**No stock clang reproduces the build**, but one configuration reproduces all seven probe
functions byte-for-byte, so the project adopts it as the **de facto pin** until proven otherwise by failing to match future reconstructions, which might then warrant a new investigation to find a better matching setting:

```text
clang 5.0.1
  -target armv8a-none-eabi -mfpu=neon-fp-armv8 -mfloat-abi=hard
  -O2 -fomit-frame-pointer -fPIC -fno-exceptions -fno-rtti
  -ffreestanding -std=c++1z
  -mllvm -pre-RA-sched=source
  -mllvm -hoist-cheap-insts=true
```

(No `-mcpu` — it was imported from the AArch64 reference projects and is wrong here;
`-mtune` is inert in clang 5.0.1's ARM32 backend. `-O2` and `-O3` are indistinguishable on
the corpus.)

### Correction — the FP feature set is ARMv8-A + NEON (supersedes the VFP-only reading)

`-mfpu=vfpv4-d16` is **too low**. Counting the whole FP/unconditional encoding space (not
only `0xEE`/`0xED`) shows the original uses ARMv8-A-only FP instructions that VFPv4 cannot
emit — `vseleq/vselgt/vselge`, `vmaxnm/vminnm`, `vrintm/vrinta`, `vcvtp` (`0xFE…`, ~2,946
words) — in ~1,041 functions, plus NEON (`0xF2`–`0xF7`, ~318 functions): ~1,259 functions
(2.93%) are unmatchable under the old pin. The old conclusion came from (a) a `0xEE`/`0xED`
-only scan that missed `0xFE` and NEON, and (b) the sole struct-copy probe, whose source hits
clang's NEON block-copy lowering. The pin is therefore `-mfpu=neon-fp-armv8` (Cortex-A57
AArch32). Recompiling the 7 probes leaves **6/7 instruction-identical**; only the struct copy
changes (clang emits NEON `vld1/vst1` for 16-byte copies, the original uses integer
`ldm/stm`). That residual is a backend difference, not a reason to disable NEON. The two
`-mllvm` knobs are still required by the other probes.

### A4 — float ABI is hardfp (`-mfloat-abi=hard`)

clang's default float ABI for `-target armv8a-none-eabi` is **softfp**: a `float` argument or
return value crosses the boundary in the integer registers `r0–r3`. The original uses the
**hardfp** ABI — floats cross in the VFP registers `s0…`. The two are mutually exclusive, so a
reconstruction that is semantically correct still fails to byte-match:

| original (hardfp) | our default (softfp) |
| --- | --- |
| `vstr.32 s0, [r0,#0x5c]` | `str r1, [r0,#0x5c]` |
| `vmov.f32 s0, #4.0` | `mov r0, #0` ; `movt r0, …` ; `vmov r0, s0` |

`-mfloat-abi=hard` reproduces the original exactly. Evidence: this was the **entire failure mass
of the first real loop run** — of 11 functions that never matched (106 attempts between them),
10 carry float parameters or returns, and all 11 byte-match once the flag is added, with the
candidate source unchanged (only the ABI differed). Re-gating the whole matched corpus (774
functions) under the flag produced **no regressions** — integer-only codegen is unaffected.

The fix must be a *pin* change, not a per-function workaround: a softfp build can never emit the
original's `vstr`/`vmov` ABI sequences, so no source rewrite can close such a diff.

> The two `-mllvm` flags are **hidden backend knobs, not real build settings**. They are a
> *reproduction device*: they make our build emit what the original emitted. They say
> nothing about the flags the vendor passed, and each is inert on any other config.

### Why no stock compiler wins

**A1 — passive fingerprint (inconclusive).** The NSO has no ELF `.comment`, so no
`clang version` banner survives. `.rodata` does carry the *build environment* baked into
the statically-linked SDK: `.../NintendoSDK/Libraries/NX-NXFP2-a32/Release/nnSdk.nss`
(SDK 4.4.2 static libs, AArch32, Windows host), `NEX … 4_4_0 … 20180117` (a **2018-01**
build image), 24× `__aeabi_*`, ARM EHABI unwinding, and RTTI. This confirms AArch32,
libc++ and a 2018 build, but does not name the compiler.

**A2 — structural fingerprint.** `.text` is ARM (A32), not Thumb (`.init_array` entries
are all even). Prologues are `stmdb sp!,{…,r11,lr}` with **no frame pointer** (`r11` is
used as a plain callee-saved scratch — a clang idiom); 1536/2325 allocate `sub sp,sp,#0x10`.
Constants use rotated `mov` / `movw` plus tail literal pools; floating point is mostly VFP
(`0xEE`/`0xED`), but the encoding space also carries ARMv8-A FP (`0xFE…`) and NEON
(`0xF2`–`0xF7`) — see the *Correction* below; the original A2 scan counted only `0xEE`/`0xED`.
These narrow the field but are shared by GCC and clang at `-O2`/`-O3`, so they cannot pin a
version.

**A3 — active reproduction.** Upstream clangs were fetched from `releases.llvm.org` and
byte-diffed against reconstructed real functions. clang **3.9.1** reproduced the 28-byte
struct copy at `0x60c70010` exactly and `-mfpu=vfpv4-d16` matched it — establishing the clang
family. (That flag was later found to be too low; see the *Correction* below.) The probe pool
then grew to **7** functions spanning several code families:

| function | addr | size |
| --- | --- | --- |
| `find_entry` (`find2`) | `0x60000f8c` | 188 |
| struct copy | `0x60c70010` | 28 |
| `find3` | `0x6069e6f0` | 100 |
| `find2s` | `0x6069eb18` | 76 |
| `findsub` | `0x6069ddfc` | 120 |
| `new_a` | `0x604f8b78` | 68 |
| `new_b` | `0x601a72e4` | 60 |

Cross-version scores (`4.0.0 ≡ 4.0.1` and `5.0.0 ≡ 5.0.1` on every probe):

| config | score | failing |
| --- | --- | --- |
| **5.0.1 `generic` + both knobs** | **7/7** | — |
| 5.0.1 `generic`, stock | 5/7 | `find2`, `new_b` |
| 5.0.1 `cortex-a57` | 5/7 | `find2`, `find3` |
| 4.0.1 / 3.9.1 / any other `-mcpu` | ≤2/7 | — |

The two residual failures are **independent backend heuristics**, not one code family:

- **`find_entry` — `MachineLICM` cheap-instruction hoist.** The `uxtb` zero-extensions the
  real build hoists into the preheader are refused by stock `generic`'s register-pressure
  gate (`hoist-cheap-insts` defaults false). `-mllvm -hoist-cheap-insts=true` hoists them
  and completes the 188/188 match.
- **`new_b` — ISel list scheduler.** The real loop body issues its load first; stock
  `generic` sinks it. `-print-before-all`/`-print-after-all` shows the first divergence is
  already at `Before Expand ISel Pseudo-instructions`, so it is the SelectionDAG list
  scheduler (`-mllvm -pre-RA-sched=source` fixes it) — not the MachineScheduler.

A stock compiler that differs from *every* stock configuration in two separate scheduling
heuristics points to a **non-stock/fork AArch32 backend** (the SSBU precedent: SDK
internals resist stock clang). clang 6.0.x was deliberately **not** chased — SDK toolchains
freeze well before a title ships, and the 2018-01 build image makes a later clang less
likely.

> Reference projects all point at a 2017-era clang (`OdysseyDecomp` and
> `Lego-City-Undercover-Decompilation` both pin 3.9.1); the 4.0/5.0 window is consistent
> with a 2018 build.

### Reproduction caveats

- **NEON is required, not a trap.** The original uses ARMv8-A FP and NEON; the pin is
  `-mfpu=neon-fp-armv8`. The only probe NEON changes is the 16-byte struct copy, where clang
  lowers to `vld1/vst1` while the original uses integer `ldm/stm` (see *Correction*).
- **Source shape matters as much as flags.** The same semantics written as
  `if (e == 0) continue; if (…) return e;` lowers to a goto state machine under 4.0.1,
  whereas `if (e != 0 && …) return e;` gives the real straight-line CFG. Reconstructions
  must reproduce the observed control flow, not merely the semantics.

### Finding leaf functions (reusable)

`tools/ghidra/DisasmFunctions.java` disassembles an address list with Ghidra's
already-selected `ARM:LE:32:v8` language (no auto-analysis needed). A pure-Python scan of
`text.bin` (opcode patterns) found **1184 call-free, relocation-free** leaf candidates —
the cleanest byte-diff targets, and a seed for the Phase 3 function corpus.
Relocation-free leaves byte-match without needing the relocation/link check.

## Which title version to target — resolved: the update

The project targets the **latest title update** (CNMT `Patch`, version `262144`), not base
`v0`. The two builds were extracted and compared:

| | Base | Update |
| --- | --- | --- |
| CNMT type | base | `Patch`, `OriginalId 0x0100770008dd8000` |
| CNMT version | `v0` | `262144` |
| ExeFS `main` SHA-256 | `876b8587…d98b02` | `b3935415…645ef` |
| ExeFS `main` size | 14,272,382 | 14,291,042 |
| Program NCA `SdkAddon Ver.` | `4.4.1 (v67371264)` | `4.4.1 (v67371264)` |

An aligned `.text` diff (`tools/nso/text_align.py`) gives **81.25%** byte overlap and a
self-consistent `insert − delete = +12,756` (exactly the file-size delta) — i.e. the
update is an **incremental patch over an otherwise-identical codebase**, not a recompile
with a new compiler. Both builds report the identical SDK, confirming the compiler did not
change.

Rationale: the repository reconstructs the **most recent released build**, so its source
corresponds to the latest code; there is no compiler-based reason to prefer base.

- Locally: `baserom/main.nso` **is the update** (`b3935415…`).
- The Ghidra project `baserom/ghidra/soaratorium` holds the update import; decompressed
  images live in `baserom/work/nso_update/` and `baserom/work/segments_update/`.
