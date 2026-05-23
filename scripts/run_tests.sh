#!/usr/bin/env bash
# Run lrc-tools test suite (stdlib unittest; TUI tests skip if textual missing)
set -euo pipefail
cd "$(dirname "$0")/.."
export LRC_TOOLS_REPO="$PWD"
echo "==> unittest (core + optional TUI)"
python3 -m unittest discover -s tests -v "$@"
