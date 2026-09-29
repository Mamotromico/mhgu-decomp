#!/usr/bin/env bash
#
# Soaratorium PoC - the end-to-end byte-match showcase.
#
# Reproduces the Phase 1 compiler-pin evidence from scratch: it imports the
# user's own NSO into Ghidra (linear, no analysis), dumps the loader-built memory
# blocks plus a disassembly of the probe entry points, compiles the reconstructed
# C++ probes with the pinned clang, and byte-compares each against the original
# .text.
#
# Nothing derived from the binary is committed: the reference .text bytes and the
# disassembly are generated into a git-ignored work dir on every run.
#
# Usage:
#   poc/run.sh [path/to/main.nso] [--show]
#
#   <nso>    defaults to baserom/main.nso
#   --show   also print the coloured side-by-side disassembly diff per probe
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${HERE}/.." && pwd)"

NSO=""
SHOW=0
for arg in "$@"; do
  case "$arg" in
    --show) SHOW=1 ;;
    -*) echo "unknown option: $arg" >&2; exit 2 ;;
    *) NSO="$arg" ;;
  esac
done
NSO="${NSO:-${ROOT}/baserom/main.nso}"

WORK="${POC_WORK:-${ROOT}/baserom/work/poc}"
GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"

PROBES="${HERE}/probes.tsv"
SRC="${HERE}/src"
LIB="${HERE}/lib"
JSCRIPTS="${ROOT}/tools/ghidra"

CLANG="${CLANG:-clang}"
CFLAGS=(
  -target armv8a-none-eabi -mfpu=vfpv4-d16
  -O2 -fomit-frame-pointer -fPIC -fno-exceptions -fno-rtti
  -ffreestanding -std=c++1z
  -mllvm -pre-RA-sched=source
  -mllvm -hoist-cheap-insts=true
)

die() { echo "error: $*" >&2; exit 1; }

[ -f "${NSO}" ] || die "NSO not found: ${NSO} (pass a path, or place it at baserom/main.nso)"
command -v "${CLANG}" >/dev/null || die "clang not found on PATH ('${CLANG}'); rebuild the devcontainer"
[ -x "${GHIDRA_HOME}/support/analyzeHeadless" ] || die "Ghidra not found at ${GHIDRA_HOME}"

echo "Soaratorium PoC"
echo "  NSO:   ${NSO}"
echo "  clang: $(${CLANG} --version | head -n1)"
echo "  work:  ${WORK}"
echo

rm -rf "${WORK}"
mkdir -p "${WORK}/segments" "${WORK}/objects"

# ---- 1. Reference bytes + disassembly, straight from the binary -------------
echo "[1/4] Importing the NSO into Ghidra and dumping reference data..."
grep -v '^#' "${PROBES}" | grep -v '^[[:space:]]*$' | cut -f3 > "${WORK}/probes.addrs"
"${GHIDRA_HOME}/support/analyzeHeadless" "${WORK}/ghidra" soaratorium \
  -import "${NSO}" -noanalysis \
  -scriptPath "${JSCRIPTS}" \
  -postScript DumpMemoryBlocks.java "${WORK}/segments" \
  -postScript DisasmFunctions.java "${WORK}/probes.addrs" "${WORK}/probes.asm" 200 \
  > "${WORK}/ghidra.log" 2>&1 || { tail -n 40 "${WORK}/ghidra.log"; die "Ghidra run failed (see ${WORK}/ghidra.log)"; }
TEXT="${WORK}/segments/.text_60000000.bin"
[ -f "${TEXT}" ] || die "expected ${TEXT}; check ${WORK}/ghidra.log"

# ---- 2. Compile each probe with the pinned clang ----------------------------
echo "[2/4] Compiling probe sources with the pinned clang..."
while IFS=$'\t' read -r name src addr size; do
  case "${name}" in ''|'#'*) continue ;; esac
  ${CLANG} "${CFLAGS[@]}" -c "${SRC}/${src}" -o "${WORK}/objects/${name}.o" \
    || die "compile failed: ${src}"
  python3 "${LIB}/textof.py" "${WORK}/objects/${name}.o" > "${WORK}/objects/${name}.bin"
  ${CLANG} "${CFLAGS[@]}" -S "${SRC}/${src}" -o "${WORK}/objects/${name}.s"
done < "${PROBES}"

# ---- 3. Byte-match + per-probe coloured diff --------------------------------
echo "[3/4] Byte-matching against the original .text..."
pass=0
total=0
while IFS=$'\t' read -r name src addr size; do
  case "${name}" in ''|'#'*) continue ;; esac
  total=$((total + 1))
  off=$(printf '%x' $(( addr - 0x60000000 )))
  out=$(python3 "${LIB}/cmpbytes.py" "${WORK}/objects/${name}.bin" "${TEXT}" "${off}" "${size}")
  rel="${name}  (${src}, ${addr}, ${size} B)"
  if printf '%s' "${out}" | grep -q '>>> MATCH'; then
    echo "  MATCH    ${rel}"
    pass=$((pass + 1))
  else
    echo "  MISMATCH ${rel}"
    printf '%s\n' "${out}" | sed 's/^/           /'
  fi
  python3 "${LIB}/show_func.py" "${WORK}/probes.asm" "${addr}" \
    > "${WORK}/objects/${name}.real.asm"
  python3 "${LIB}/matchdiff.py" "${WORK}/objects/${name}.real.asm" "${TEXT}" \
    "${off}" "${size}" "${WORK}/objects/${name}.s" "${WORK}/objects/${name}.bin" \
    > "${WORK}/objects/${name}.diff.txt" 2>&1 || true
  if [ "${SHOW}" -eq 1 ]; then
    echo
    sed 's/^/    /' "${WORK}/objects/${name}.diff.txt"
  fi
done < "${PROBES}"

# ---- 4. Summary -------------------------------------------------------------
echo
echo "[4/4] Result: ${pass}/${total} probes byte-match the original build."
echo "      Coloured diffs: ${WORK}/objects/<probe>.diff.txt"
[ "${pass}" -eq "${total}" ]
