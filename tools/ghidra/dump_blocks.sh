#!/usr/bin/env bash
#
# Soaratorium — dump the loader-built memory blocks of the NSO.
#
# Imports the NSO into a throwaway Ghidra project with -noanalysis (the Switch loader
# builds the memory map at import; no analysis is needed to read blocks) and runs
# DumpMemoryBlocks.java, writing one <block>_<startHex>.bin per initialized block.
#
# This is the reference-byte source for tools/ledger/bytegate.py; it is called per check.
# A fresh throwaway project every run keeps it lock-free and deterministic.
#
# Usage:
#   tools/ghidra/dump_blocks.sh [path/to/main.nso] [outdir]
#
# Env:
#   GHIDRA_HOME  Ghidra install (default /opt/ghidra)
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${HERE}/../.." && pwd)"

NSO="${1:-${ROOT}/baserom/main.nso}"
OUT="${2:-${ROOT}/baserom/work/memoryblocks}"
GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"

die() { echo "error: $*" >&2; exit 1; }

[ -f "${NSO}" ] || die "NSO not found: ${NSO}"
[ -x "${GHIDRA_HOME}/support/analyzeHeadless" ] || die "Ghidra not found at ${GHIDRA_HOME}"

PROJ="$(dirname "${OUT}")/ghidra_dump"
rm -rf "${PROJ}" "${OUT}"
mkdir -p "${PROJ}" "${OUT}"

"${GHIDRA_HOME}/support/analyzeHeadless" "${PROJ}" blocks \
  -import "${NSO}" -noanalysis \
  -scriptPath "${HERE}" \
  -postScript DumpMemoryBlocks.java "${OUT}" \
  > "${OUT}/dump.log" 2>&1 \
  || { tail -n 40 "${OUT}/dump.log"; die "Ghidra run failed (see ${OUT}/dump.log)"; }

echo "dumped memory blocks to ${OUT}"
