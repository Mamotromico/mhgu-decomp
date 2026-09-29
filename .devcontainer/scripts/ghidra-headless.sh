#!/usr/bin/env bash
# Headless Ghidra wrapper — for automation, GhidraMCP, and agent-driven analysis
# (no GUI/display needed). Passes arguments straight to analyzeHeadless.
set -euo pipefail

GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"

exec "${GHIDRA_HOME}/support/analyzeHeadless" "$@"
