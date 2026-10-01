# Inventory export (Phase 3 — the ledger seed)

The deterministic Ghidra export that **seeds the committed symbol ledger**. It is a *draft*:
Ghidra never decides identity, boundaries, names, or the progress denominator — it proposes
cut points, and the committed ledger (hand-owned) stays authoritative. See
[`architecture.md`](architecture.md) → *Segmentation seed* and *Ledger & export format*.

Everything this produces is **binary-derived metadata** and lands in the git-ignored
`baserom/work/inventory/` tree. It is **never committed** (see [`AGENTS.md`](../AGENTS.md) →
*Repository hygiene*).

## Running it

```sh
tools/ghidra/inventory.sh              # warm: reuse the cached analysis
tools/ghidra/inventory.sh --reanalyze  # (re)run full auto-analysis first
```

- **Cold** (no cached program): imports `baserom/main.nso` and runs a full auto-analysis. Slow.
- **Warm** (program cached): re-runs only the export script. Fast.
- **`--reanalyze`**: re-runs auto-analysis over the cached program. Required **once** if the
  project was previously imported without analysis (e.g. by the PoC's `-noanalysis` import).

A loader-only (`-noanalysis`) import has no functions, so the export is nearly empty — always
analyse before trusting the output.

Overridable via environment: `GHIDRA_HOME`, `PROJ_DIR`, `PROJ_NAME`, `PROGRAM`,
`INVENTORY_OUT`.

## Outputs

All three files are **TSV with a header row**, one record per line, sorted deterministically
(by address, then name). Addresses are 8-digit lowercase hex, offset from the image base.

### `inventory.tsv` — cut-point candidates → the ledger manifest

| column | meaning |
| --- | --- |
| `addr` | symbol address (blank for externals) |
| `kind` | `function` \| `data` \| `external` |
| `size` | bytes (function body length, or data length; `0` when unknown) |
| `name` | Ghidra's raw name, **verbatim** (provenance, not identity — see below) |
| `block` | memory block name (library namespace for externals) |
| `source` | `Symbol.getSource()` — `DEFAULT` \| `ANALYSIS` \| `IMPORTED` \| `USER_DEFINED` |
| `name_class` | `discovered` \| `generated` (derived, see *Classification*) |
| `thunk` `entry` `exported` `noncontig` | `0`/`1` function flags |

### `inventory.nested.tsv` — reference-only symbols → the review table

Never the manifest (a nested entry would re-split a segment; see *Symbol identity &
segmentation*). Columns: `addr`, `kind` (`data`\|`label`\|`field`), `size`, `name`, `block`,
`source`, `name_class`, `reason` (`in_function` \| `field` \| `label`).

### `inventory.gaps.tsv` — uncovered ranges

Contiguous coverage of every **initialized** block (bss and other uninitialized blocks are
skipped — no bytes to match). Columns: `block`, `start`, `end`, `size`. The ledger generator
fills these with address-named `D_<addr>` blobs so the denominator is complete.

## Classification rules

- **Functions** (symbols at a function entry) → cut points, `kind = function`.
- **Top-level data** (a `Data` object starting at the symbol, *outside* any function body) →
  cut points, `kind = data`.
- **Data or labels inside a function body** (literal pools, jump tables, branch labels) →
  nested, `reason = in_function`.
- **Fields** strictly inside a larger `Data` object → nested, `reason = field`.
- **Bare labels** with no data → nested, `reason = label`.
- **Externals** come from `ExternalManager.getExternalLocations()` and are listed after the
  in-memory symbols, `kind = external`.
- **One row per symbol; no de-duplication.** Alias resolution is the *ledger generator's* job
  (via the `is_alias` guard), not the export's.

**`name_class`** is `discovered` when the name came from the binary or a human
(`IMPORTED`/`USER_DEFINED`) and `generated` otherwise (`DEFAULT`/`ANALYSIS`). It is derived
from `Symbol.getSource()` and symbol type, **never** by string-matching the `FUN_`/`DAT_`
prefix — the prefix is Ghidra's *inference* and can shift across analysis runs.

Data is enumerated **where a reference points at it**, so computed-offset blobs can be missed
and boundaries inferred: the export *seeds* the ledger, it does not bound it. The
`getDefinedData` firehose (every byte Ghidra happens to type) is deliberately **not** walked —
that would balloon the denominator with speculative typing. Whatever is genuinely uncovered
shows up in `inventory.gaps.tsv` instead.

## Determinism

The output depends solely on the pinned trio — **Ghidra 12.1.2, the Switch Loader, and the
NSO** — plus sort order. No timestamps, no absolute paths, no machine state. Two runs over the
same inputs are byte-identical.

## Open item

External **binding** (weak / `lazy`) is a linker attribute the ledger needs, but it is not yet
emitted: it depends on what the loader actually surfaces. Verify against the loader's external
symbols before adding a `binding` column.
