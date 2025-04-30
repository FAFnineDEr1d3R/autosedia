#!/usr/bin/env bash
set -euo pipefail

# === Configuration ===
PYTHON_VERSION="3.11.7"
VENV_NAME="autosedia_venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ_FILE="$SCRIPT_DIR/requirements.txt"

# === Helper: print & run ===
run() {
  echo "▶ $*"
  "$@"
}

# === 1. Ensure pyenv is installed ===
if command -v pyenv >/dev/null 2>&1; then
  echo "pyenv detected, skipping installation"
else
  echo "pyenv not found, installing…"
  OS="$(uname)"
  if [[ "$OS" == "Darwin" ]]; then
    # macOS: install via Homebrew
    if ! command -v brew >/dev/null 2>&1; then
      echo "Homebrew not found. Please install Homebrew first: https://brew.sh/"
      exit 1
    fi
    echo "Updating Homebrew & installing pyenv"
    brew update
    brew install pyenv

  elif [[ "$OS" == "Linux" ]]; then
    # Linux: install build essentials & pyenv
    echo "Installing build tools and dependencies"
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y
    elif command -v yum >/dev/null 2>&1; then
      sudo yum groupinstall -y "Development Tools"
      sudo yum install -y
    else
      echo "Neither apt-get nor yum found; please install dependencies manually." >&2
    fi
    echo "Bootstrapping pyenv installer"
    curl https://pyenv.run | bash

  else
    echo "Unsupported OS: $OS" >&2
    exit 1
  fi
fi

# === 2. Initialize pyenv in this shell ===
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

# === 3. Ensure Python $PYTHON_VERSION ===
echo "Checking for Python $PYTHON_VERSION …"
PYBIN=""
if command -v python3.11 >/dev/null 2>&1; then
  INSTALLED="$(python3.11 --version 2>&1 | awk '{print $2}')"
  if [[ "$INSTALLED" == "$PYTHON_VERSION" ]]; then
    PYBIN="$(command -v python3.11)"
    echo "System python3.11 ($INSTALLED) found"
  else
    echo "System python3.11 is $INSTALLED, need $PYTHON_VERSION"
  fi
fi

if [[ -z "$PYBIN" ]]; then
  echo "→ Installing Python $PYTHON_VERSION via pyenv…"
  pyenv install -s "$PYTHON_VERSION"
  PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
  PYBIN="$PYENV_ROOT/versions/$PYTHON_VERSION/bin/python"
fi

# === 4. Create virtual environment ===
VENV_PATH="$SCRIPT_DIR/$VENV_NAME"
echo "==> Creating virtual environment at $VENV_PATH"
run "$PYBIN" -m venv "$VENV_PATH"

# === 4b. Ensure `python` and `pip` commands exist in the venv ===
if [[ ! -x "$VENV_PATH/bin/python" && -x "$VENV_PATH/bin/python3" ]]; then
  echo "→ Adding 'python' → 'python3' symlink in venv"
  run ln -sf python3 "$VENV_PATH/bin/python"
fi
if [[ ! -x "$VENV_PATH/bin/pip" && -x "$VENV_PATH/bin/pip3" ]]; then
  echo "→ Adding 'pip' → 'pip3' symlink in venv"
  run ln -sf pip3 "$VENV_PATH/bin/pip"
fi

# === 5. Activate & install dependencies ===
echo "==> Activating venv and installing dependencies"
# shellcheck disable=SC1090
source "$VENV_PATH/bin/activate"
run pip install --upgrade pip
if [[ -f "$REQ_FILE" ]]; then
  run pip install -r "$REQ_FILE"
else
  echo "requirements.txt not found at $REQ_FILE"
fi

# === 6. Deactivate ===
deactivate
echo "Setup complete!"