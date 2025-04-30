#!/usr/bin/env bash
set -euo pipefail

# ——————————————————————————————
# run_autosedia.sh
# Activates autosedia_venv, runs autosedia.py, then deactivates
# Usage: ./run_autosedia.sh [args...]
# ——————————————————————————————

# 1. Find script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/autosedia_venv"
PY_SCRIPT="$SCRIPT_DIR/autosedia.py"

# 2. Check that venv and script exist
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Virtual environment not found at $VENV_DIR"
  echo "Please run the setup script first to create autosedia_venv."
  exit 1
fi

if [[ ! -f "$PY_SCRIPT" ]]; then
  echo "autosedia.py not found at $PY_SCRIPT"
  exit 1
fi

# 3. Define cleanup to deactivate venv on exit
cleanup() {
  # only try to deactivate if the function exists (i.e., venv was activated)
  if type deactivate >/dev/null 2>&1; then
    deactivate
    echo "Virtual environment deactivated."
  fi
}
trap cleanup EXIT

# 4. Activate venv
source "$VENV_DIR/bin/activate"
echo "Activated virtual environment."

# 5. Run the Python script with any provided arguments
echo "▶ Running autosedia.py"
python "$PY_SCRIPT" "$@"

# (When this script exits, cleanup() will run and deactivate the venv)
echo "autosedia.py finished."
