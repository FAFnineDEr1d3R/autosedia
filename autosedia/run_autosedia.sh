#!/usr/bin/env bash
set -euo pipefail

# ——————————————————————————————————————————
# run_autosedia.sh
# Activates autosedia_venv, runs autosedia.py, then deactivates
# Logs everything to autosedia_run.log and tails it in a new terminal
# Usage: ./run_autosedia.sh [args...]
# ——————————————————————————————————————————

# 1. Find script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AUTOSEDIA_SCRIPT_DIR="$SCRIPT_DIR" # so autosedia.py can access correct directory
VENV_DIR="$SCRIPT_DIR/autosedia_venv"
PY_SCRIPT="$SCRIPT_DIR/autosedia.py"

# === SET UP RUN LOG + LIVE TAIL ===
RUN_LOG="$SCRIPT_DIR/autosedia_run.log"
: > "$RUN_LOG"  # truncate or create the run log

OS="$(uname)"
if [[ "$OS" == "Darwin" ]]; then
  # macOS: open Terminal.app and tail the log
  osascript <<EOF
tell application "Terminal"
  do script "tail -f \"$RUN_LOG\""
  activate
end tell
EOF

elif [[ "$OS" == "Linux" ]]; then
  # Linux: try gnome-terminal, then xterm
  if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal -- bash -c "tail -f \"$RUN_LOG\"; exec bash" &
  elif command -v xterm >/dev/null 2>&1; then
    xterm -e "tail -f \"$RUN_LOG\"" &
  else
    echo "⚠ Could not open a new terminal for live log. Please run: tail -f $RUN_LOG" >&2
  fi
fi

# Redirect ALL stdout & stderr from here on into the run log
exec > "$RUN_LOG" 2>&1

# === 2. Check that venv and script exist ===
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Virtual environment not found at $VENV_DIR"
  exit 1
fi
if [[ ! -f "$PY_SCRIPT" ]]; then
  echo "Python script not found at $PY_SCRIPT"
  exit 1
fi

# === 3. Cleanup function (runs on exit) ===
cleanup() {
  deactivate 2>/dev/null || true
  echo "Virtual environment deactivated."
}
trap cleanup EXIT

# === 4. Activate venv ===
source "$VENV_DIR/bin/activate"
echo "Activated virtual environment."

# === 5. Run the Python script ===
echo "▶ Running autosedia.py with args: $*"
python -u "$PY_SCRIPT" "$@" # the -u will do unbuffered version so all text in .py is printed to logfile/terminal

echo "autosedia.py finished."