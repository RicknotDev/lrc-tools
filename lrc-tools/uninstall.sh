#!/usr/bin/env bash
set -euo pipefail

echo "=============================="
echo " lrc-tools uninstall"
echo "=============================="
echo
python3 -m pip uninstall lrc-tools "$@"
