#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-macos-build"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script must run on macOS."
  exit 1
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install pyinstaller

cd "$ROOT_DIR"
pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name MelodyLogicBuilder \
  melody_architect/gui.py

mkdir -p "$ROOT_DIR/dist/macos"
cp -R "$ROOT_DIR/dist/MelodyLogicBuilder.app" "$ROOT_DIR/dist/macos/"
cp "$ROOT_DIR/packaging/macos/README_MAC_APP.md" "$ROOT_DIR/dist/macos/"
cp "$ROOT_DIR/packaging/macos/open_terminal_cli.command" "$ROOT_DIR/dist/macos/"
chmod +x "$ROOT_DIR/dist/macos/open_terminal_cli.command"

echo "Build complete: $ROOT_DIR/dist/macos"
