#!/usr/bin/env bash
#
# mhgu-decomp — inventory export driver (Phase 3, first step).
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

usage() {
  cat <<'EOF'
Usage: inventory.sh [--reanalyze] [path/to/main.nso]

Run a full Ghidra auto-analysis (cached under baserom/ghidra/) and export the
post-analysis symbol universe as deterministic TSVs under baserom/work/inventory/.

  --reanalyze  re-run auto-analysis over the cached program before exporting
               (required once if the project was imported without analysis)
  <nso>        NSO image (default baserom/main.nso)

Env:
  GHIDRA_HOME  Ghidra install (default /opt/ghidra)
  INV_WORK     export output dir (default baserom/work/inventory)
  PROGRAM      cached program name (default: the NSO's basename)
EOF
}

die() { echo "error: $*" >&2; exit 1; }

REANALYZE=0
POS=()
for arg in "$@"; do
  case "${arg}" in
    -h|--help) usage; exit 0 ;;
    --reanalyze) REANALYZE=1 ;;
    -*) echo "error: unknown option: ${arg}" >&2; usage >&2; exit 2 ;;
    *) POS+=("${arg}") ;;
  esac
done
[ "${#POS[@]}" -le 1 ] || die "too many arguments (see --help)"

NSO="${POS[0]:-${ROOT}/baserom/main.nso}"

GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"
WORK="${INV_WORK:-${ROOT}/baserom/work/inventory}"
PROJ_LOC="${ROOT}/baserom/ghidra"
PROJ_NAME="mhgu-decomp"
PROGRAM="${PROGRAM:-$(basename "${NSO}")}"

# Full analysis over a ~14 MB image overruns Ghidra's 2G headless default.
export GHIDRA_HEADLESS_MAXMEM="${GHIDRA_HEADLESS_MAXMEM:-8G}"

[ -f "${NSO}" ] || die "NSO not found: ${NSO} (pass a path, or place it at baserom/main.nso)"
[ -x "${GHIDRA_HOME}/support/analyzeHeadless" ] || die "Ghidra not found at ${GHIDRA_HOME}"

mkdir -p "${WORK}" "${PROJ_LOC}"
ANALYZE="${GHIDRA_HOME}/support/analyzeHeadless"

if [ -d "${PROJ_LOC}/${PROJ_NAME}.rep" ]; then
  if [ "${REANALYZE}" -eq 1 ]; then
    echo "mhgu-decomp inventory (reanalyze: re-run full auto-analysis on cached program — slow)"
  else
    echo "mhgu-decomp inventory (warm: reuse cached analysis)"
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
      || { tail -n 40 "${WORK}/inventory.log" >&2; die "Ghidra run failed (see ${WORK}/inventory.log)"; }
  else
    # Warm export only reads the cached program, so open it read-only: no save is
    # attempted (the export never mutates the program), which removes the post-run
    # save/index-flush failure mode entirely.
    "${ANALYZE}" "${PROJ_LOC}" "${PROJ_NAME}" \
      -process "${PROGRAM}" -noanalysis -readOnly \
      -scriptPath "${HERE}" \
      -postScript InventoryExport.java "${WORK}" \
      > "${WORK}/inventory.log" 2>&1 \
      || { tail -n 40 "${WORK}/inventory.log" >&2; die "Ghidra run failed (see ${WORK}/inventory.log)"; }
  fi
else
  if [ "${REANALYZE}" -eq 1 ]; then
    echo "note: --reanalyze has no effect on a cold run (no cached project; analysis is implied)" >&2
  fi
  echo "mhgu-decomp inventory (cold: import + full auto-analysis — this is slow)"
  echo "  NSO:     ${NSO}"
  echo "  project: ${PROJ_LOC}/${PROJ_NAME}"
  echo "  work:    ${WORK}"
  echo
  "${ANALYZE}" "${PROJ_LOC}" "${PROJ_NAME}" \
    -import "${NSO}" \
    -scriptPath "${HERE}" \
    -postScript InventoryExport.java "${WORK}" \
    > "${WORK}/inventory.log" 2>&1 \
    || { tail -n 40 "${WORK}/inventory.log" >&2; die "Ghidra run failed (see ${WORK}/inventory.log)"; }
fi

# A header-only (or missing) inventory means the export found no functions — the
# classic "warm run over an un-analysed program" failure. Refuse to present it as success.
if [ ! -s "${WORK}/inventory.tsv" ] || [ "$(wc -l < "${WORK}/inventory.tsv")" -lt 2 ]; then
  echo "error: no functions in ${WORK}/inventory.tsv" >&2
  echo "       the cached program may be un-analysed — re-run with --reanalyze" >&2
  tail -n 20 "${WORK}/inventory.log" >&2
  exit 1
fi

echo
echo "Wrote (see InventoryExport.java for schema):"
for f in inventory.tsv inventory.nested.tsv inventory.gaps.tsv inventory.externals.tsv; do
  [ -f "${WORK}/${f}" ] && printf '  %-24s %s rows\n' "${f}" "$(wc -l < "${WORK}/${f}")"
done
echo "Log: ${WORK}/inventory.log"
