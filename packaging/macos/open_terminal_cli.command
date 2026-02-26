#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$ROOT_DIR"
if command -v python3 >/dev/null 2>&1; then
  python3 -m melody_architect --help
else
  echo "python3 not found"
  exit 1
fi

echo
echo "Example:"
echo "python3 -m melody_architect logic-kit INPUT.wav --style pop --project-name 'My Song' --output-dir ./logic_export"
