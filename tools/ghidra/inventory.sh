#!/usr/bin/env bash
#
# Soaratorium — inventory export driver (Phase 3, first step).
#
# Runs a FULL Ghidra auto-analysis of the user's NSO (cold: import + analyze +
# export in one pass) and writes the post-analysis symbol universe to
# git-ignored <WORK>/ as four deterministic TSVs — see InventoryExport.java for
# the schema and classification rules.
#
# The analysis is cached in a Ghidra project under baserom/ghidra/; later runs
# are "warm" (reuse the project, skip re-analysis) and only re-run the export
# script. Both baserom/ghidra/ and baserom/work/ are git-ignored wholesale.
#
# Usage:
#   tools/ghidra/inventory.sh [path/to/main.nso]
#
#   <nso>    defaults to baserom/main.nso
#
# Env overrides:
#   GHIDRA_HOME  Ghidra install (default /opt/ghidra)
#   INV_WORK     export output dir (default baserom/work/inventory)
#   PROGRAM      program name for warm runs (default main — Ghidra names the
#                imported domain file after the NSO's basename; override only
#                if the loader chose a different name)
#
# NOTE: the cold run performs a full auto-analysis of a ~14 MB AArch32 image and
# can take a long time. It is a one-time cost; warm runs are fast.
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${HERE}/../.." && pwd)"

NSO="${1:-${ROOT}/baserom/main.nso}"

GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"
WORK="${INV_WORK:-${ROOT}/baserom/work/inventory}"
PROJ_LOC="${ROOT}/baserom/ghidra"
PROJ_NAME="soaratorium"
PROGRAM="${PROGRAM:-main}"

die() { echo "error: $*" >&2; exit 1; }

[ -f "${NSO}" ] || die "NSO not found: ${NSO} (pass a path, or place it at baserom/main.nso)"
[ -x "${GHIDRA_HOME}/support/analyzeHeadless" ] || die "Ghidra not found at ${GHIDRA_HOME}"

mkdir -p "${WORK}" "${PROJ_LOC}"
ANALYZE="${GHIDRA_HOME}/support/analyzeHeadless"

if [ -d "${PROJ_LOC}/${PROJ_NAME}.rep" ]; then
  echo "Soaratorium inventory (warm: reuse cached analysis)"
  echo "  project: ${PROJ_LOC}/${PROJ_NAME}  program: ${PROGRAM}"
  echo "  work:    ${WORK}"
  echo
  "${ANALYZE}" "${PROJ_LOC}" "${PROJ_NAME}" \
    -process "${PROGRAM}" -noanalysis \
    -scriptPath "${HERE}" \
    -postScript InventoryExport.java "${WORK}" \
    > "${WORK}/inventory.log" 2>&1 \
    || { tail -n 40 "${WORK}/inventory.log"; die "Ghidra run failed (see ${WORK}/inventory.log)"; }
else
  echo "Soaratorium inventory (cold: import + full auto-analysis — this is slow)"
  echo "  NSO:     ${NSO}"
  echo "  project: ${PROJ_LOC}/${PROJ_NAME}"
  echo "  work:    ${WORK}"
  echo
  "${ANALYZE}" "${PROJ_LOC}" "${PROJ_NAME}" \
    -import "${NSO}" \
    -scriptPath "${HERE}" \
    -postScript InventoryExport.java "${WORK}" \
    > "${WORK}/inventory.log" 2>&1 \
    || { tail -n 40 "${WORK}/inventory.log"; die "Ghidra run failed (see ${WORK}/inventory.log)"; }
fi

echo
echo "Wrote (see InventoryExport.java for schema):"
for f in inventory.tsv inventory.nested.tsv inventory.gaps.tsv inventory.externals.tsv; do
  [ -f "${WORK}/${f}" ] && printf '  %-24s %s rows\n' "${f}" "$(wc -l < "${WORK}/${f}")"
done
echo "Log: ${WORK}/inventory.log"
