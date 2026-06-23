#!/usr/bin/env bash
# lrc-tools setup — delegates to install.sh
# For Windows, use: powershell -ExecutionPolicy Bypass -File install.ps1
set -euo pipefail

cd "$(dirname "$0")"

if [[ "$(uname -s)" == MINGW* || "$(uname -s)" == CYGWIN* || "$(uname -s)" == MSYS* ]]; then
    echo "On Windows, use install.ps1 (PowerShell) instead:"
    echo "  powershell -ExecutionPolicy Bypass -File install.ps1"
    exit 0
fi

INSTALL_SPEC='.[full]'
if [[ "${1:-}" == "--minimal" ]]; then
    INSTALL_SPEC='.'
    shift
fi

exec bash install.sh "${INSTALL_SPEC}" "$@"
