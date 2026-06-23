#!/usr/bin/env bash
# Run lrc-tools test suite (stdlib unittest; TUI tests skip if textual missing)
# Works on Linux, macOS, and Windows (Git Bash / WSL)
set -euo pipefail
cd "$(dirname "$0")/.."
export LRC_TOOLS_REPO="$PWD"
PYTHON="${PYTHON:-python3}"
if command -v "$PYTHON" &>/dev/null; then
  :
elif command -v python &>/dev/null; then
  PYTHON=python
else
  echo "Error: Python not found. Set PYTHON env var or install Python 3.12+."
  exit 1
fi
echo "==> unittest (core + optional TUI)"
$PYTHON -m unittest discover -s tests -v "$@"
