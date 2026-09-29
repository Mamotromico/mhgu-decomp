#!/usr/bin/env bash
# Launch Ghidra's GUI from inside the devcontainer.
#
# Two access modes:
#   1. noVNC (default, cross-platform):
#        ./ghidra-gui.sh vnc
#        then open http://localhost:6080/vnc.html in a browser.
#   2. X11 (Linux host only — requires the X socket + DISPLAY configured in
#        devcontainer.json):
#        ./ghidra-gui.sh x11
set -euo pipefail

GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"

mode="${1:-vnc}"

case "$mode" in
  x11)
    exec "${GHIDRA_HOME}/ghidraRun"
    ;;

  vnc)
    # Virtual framebuffer + VNC + noVNC, then Ghidra on the virtual display.
    Xvfb :1 -screen 0 1280x800x24 &
    x11vnc -display :1 -forever -nopw -shared -quiet &
    websockify --web /usr/share/novnc/ 6080 localhost:5900 &
    DISPLAY=:1 exec "${GHIDRA_HOME}/ghidraRun"
    ;;

  *)
    echo "usage: $0 [vnc|x11]" >&2
    exit 2
    ;;
esac
