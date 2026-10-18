#!/usr/bin/env bash
#
# mhgu-decomp — dump the loader-built memory blocks of the NSO.
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

usage() {
  cat <<'EOF'
Usage: dump_blocks.sh [path/to/main.nso] [outdir]

Dump the loader-built memory blocks of an NSO0 image to <outdir> as
<block>_<startHex>.bin, one file per initialized block.

  <nso>      NSO image        (default baserom/main.nso)
  <outdir>   output directory (default baserom/work/memoryblocks)

Env:
  GHIDRA_HOME  Ghidra install (default /opt/ghidra)
EOF
}

die() { echo "error: $*" >&2; exit 1; }

POS=()
for arg in "$@"; do
  case "${arg}" in
    -h|--help) usage; exit 0 ;;
    -*) echo "error: unknown option: ${arg}" >&2; usage >&2; exit 2 ;;
    *) POS+=("${arg}") ;;
  esac
done
[ "${#POS[@]}" -le 2 ] || die "too many arguments (see --help)"

NSO="${POS[0]:-${ROOT}/baserom/main.nso}"
OUT="${POS[1]:-${ROOT}/baserom/work/memoryblocks}"
GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"
ANALYZE="${GHIDRA_HOME}/support/analyzeHeadless"

[ -f "${NSO}" ] || die "NSO not found: ${NSO}"
[ -x "${ANALYZE}" ] || die "Ghidra not found at ${GHIDRA_HOME}"

PROJ="$(dirname "${OUT}")/ghidra_dump"
# The project only exists for this one import; never leave it behind.
trap 'rm -rf "${PROJ}"' EXIT
rm -rf "${PROJ}" "${OUT}"
mkdir -p "${PROJ}" "${OUT}"

echo "dumping blocks: ${NSO}"
echo "  project: ${PROJ} (throwaway)"
echo "  out:     ${OUT}"

"${ANALYZE}" "${PROJ}" blocks \
  -import "${NSO}" -noanalysis \
  -scriptPath "${HERE}" \
  -postScript DumpMemoryBlocks.java "${OUT}" \
  > "${OUT}/dump.log" 2>&1 \
  || { tail -n 40 "${OUT}/dump.log" >&2; die "Ghidra run failed (see ${OUT}/dump.log)"; }

# analyzeHeadless can exit 0 even when the script bailed (e.g. bad args), so require output.
# Block files are named after blocks like ".text", i.e. dotfiles, so a shell glob
# ("*.bin") would not match them; count with find (its name match ignores the dot).
COUNT="$(find "${OUT}" -maxdepth 1 -name '*.bin' | wc -l)"
if [ "${COUNT}" -eq 0 ]; then
  tail -n 40 "${OUT}/dump.log" >&2
  die "no memory blocks were dumped (see ${OUT}/dump.log)"
fi

echo "dumped ${COUNT} memory block(s) to ${OUT}"
echo "log: ${OUT}/dump.log"
