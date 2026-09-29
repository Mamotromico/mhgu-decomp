# poc — byte-match showcase

A self-contained proof-of-concept that reproduces the Phase 1 compiler evidence
from scratch: it reconstructs seven real functions as C++, compiles them with the
pinned toolchain, and byte-compares each result against the original `.text`.

It is the smallest end-to-end example of the project's central claim — *the
binary is truth* — and doubles as a harness for learning the toolchain idioms.

## Run it

Supply your own copy of the game's `main` executable (see the root README), then:

```sh
poc/run.sh                       # uses baserom/main.nso
poc/run.sh path/to/main.nso      # explicit path
poc/run.sh --show                # also print per-probe coloured diffs
```

Expected final line:

```text
[4/4] Result: 7/7 probes byte-match the original build.
```

## What it does

1. **Import** — `analyzeHeadless` loads the NSO into a throwaway Ghidra project
   with the Switch loader, `-noanalysis` (the loader picks `ARM:LE:32:v8` and
   builds the memory map at import).
2. **Reference data** — two Ghidra scripts dump the loader-built memory blocks
   (`DumpMemoryBlocks.java` → `.text_60000000.bin`) and a linear disassembly of
   the probe entry points (`DisasmFunctions.java`).
3. **Compile** — each probe under `src/` is built with the pinned clang and the
   de facto pin flags (see `AGENTS.md`), then its `.text` bytes are extracted
   (`lib/textof.py`; no `llvm-objcopy` needed).
4. **Match** — the bytes are diffed against the original at the recorded offset
   (`lib/cmpbytes.py`), and a byte-grounded coloured disassembly diff is written
   per probe (`lib/matchdiff.py`).

## Nothing here is derived from the binary

The reconstructed C++ under `src/` is the project's own output and is committed.
The *reference* data — the decompressed `.text` and the disassembly — is
**generated on every run** into a git-ignored work directory
(`baserom/work/poc/`) from the developer's own copy of the executable. No bytes
or listing from the original binary are stored in this repository.

## Files

| path | role |
| --- | --- |
| `run.sh` | entry point; orchestrates the whole pipeline |
| `probes.tsv` | probe table: name, source, address, size |
| `src/*.cpp` | reconstructed functions (the committed artifact) |
| `lib/cmpbytes.py` | byte-for-byte compare of a compiled `.text` blob vs the original |
| `lib/textof.py` | extract an ELF section's bytes without `llvm-objcopy` |
| `lib/matchdiff.py` | coloured instruction-level diff (real disasm vs compiled) |
| `lib/show_func.py` | slice one `;; entry` block out of a combined disassembly |

## Caveats

- The two `-mllvm` knobs in `run.sh` are **hidden backend diagnostics, not build
  settings** — they are a reproduction device for the de facto pin, not what the
  vendor passed. See `AGENTS.md` / `docs/compiler-identification.md`.
- The probe addresses are specific to the targeted title version; they are not
  game data, but a different build will not match.
