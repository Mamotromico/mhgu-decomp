#!/usr/bin/env bash
#
# Soaratorium — inventory export driver (Phase 3, first step).
#
# Runs a FULL Ghidra auto-analysis of the user's NSO and writes the post-analysis
# symbol universe to git-ignored <WORK>/ as four deterministic TSVs — see
# InventoryExport.java for the schema and classification rules.
#
# The analysis is cached in a Ghidra project under baserom/ghidra/; later runs
# are "warm" (reuse the project, skip re-analysis) and only re-run the export
# script. Both baserom/ghidra/ and baserom/work/ are git-ignored wholesale.
#
# Usage:
#   tools/ghidra/inventory.sh [--reanalyze] [path/to/main.nso]
#
#   --reanalyze  re-run auto-analysis over the *cached* program before exporting.
#                Required once if the project was previously imported without
#                analysis (e.g. by an import-only/-noanalysis run): a warm export
#                over an un-analysed program is near-empty and must not be trusted.
#   <nso>        defaults to baserom/main.nso
#
# Env overrides:
#   GHIDRA_HOME  Ghidra install (default /opt/ghidra)
#   INV_WORK     export output dir (default baserom/work/inventory)
#   PROGRAM      program name for warm runs (default: the NSO's basename —
#                Ghidra names the imported domain file after it, e.g. main.nso;
#                override only if the loader chose a different name)
#
# NOTE: the cold/reanalyze runs perform a full auto-analysis of a ~14 MB AArch32
# image and can take a long time (~30 min). It is a one-time cost; warm runs are
# fast. The heap is raised by default because full analysis overruns Ghidra's
# 2G default.
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${HERE}/../.." && pwd)"

REANALYZE=0
if [ "${1:-}" = "--reanalyze" ]; then
  REANALYZE=1
  shift
fi
NSO="${1:-${ROOT}/baserom/main.nso}"

GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"
WORK="${INV_WORK:-${ROOT}/baserom/work/inventory}"
PROJ_LOC="${ROOT}/baserom/ghidra"
PROJ_NAME="soaratorium"
PROGRAM="${PROGRAM:-$(basename "${NSO}")}"

# Full analysis over a ~14 MB image overruns Ghidra's 2G headless default.
export GHIDRA_HEADLESS_MAXMEM="${GHIDRA_HEADLESS_MAXMEM:-8G}"

die() { echo "error: $*" >&2; exit 1; }

[ -f "${NSO}" ] || die "NSO not found: ${NSO} (pass a path, or place it at baserom/main.nso)"
[ -x "${GHIDRA_HOME}/support/analyzeHeadless" ] || die "Ghidra not found at ${GHIDRA_HOME}"

mkdir -p "${WORK}" "${PROJ_LOC}"
ANALYZE="${GHIDRA_HOME}/support/analyzeHeadless"

if [ -d "${PROJ_LOC}/${PROJ_NAME}.rep" ]; then
  if [ "${REANALYZE}" -eq 1 ]; then
    echo "Soaratorium inventory (reanalyze: re-run full auto-analysis on cached program — slow)"
  else
    echo "Soaratorium inventory (warm: reuse cached analysis)"
  fi
  echo "  project: ${PROJ_LOC}/${PROJ_NAME}  program: ${PROGRAM}"
  echo "  work:    ${WORK}"
  echo
  if [ "${REANALYZE}" -eq 1 ]; then
    "${ANALYZE}" "${PROJ_LOC}" "${PROJ_NAME}" \
      -process "${PROGRAM}" \
      -scriptPath "${HERE}" \
      -postScript InventoryExport.java "${WORK}" \
      > "${WORK}/inventory.log" 2>&1 \
      || { tail -n 40 "${WORK}/inventory.log"; die "Ghidra run failed (see ${WORK}/inventory.log)"; }
  else
    # Warm export only reads the cached program, so open it read-only: no save is
    # attempted (the export never mutates the program), which removes the post-run
    # save/index-flush failure mode entirely.
    "${ANALYZE}" "${PROJ_LOC}" "${PROJ_NAME}" \
      -process "${PROGRAM}" -noanalysis -readOnly \
      -scriptPath "${HERE}" \
      -postScript InventoryExport.java "${WORK}" \
      > "${WORK}/inventory.log" 2>&1 \
      || { tail -n 40 "${WORK}/inventory.log"; die "Ghidra run failed (see ${WORK}/inventory.log)"; }
  fi
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
