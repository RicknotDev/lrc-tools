#!/usr/bin/env bash
set -euo pipefail

INSTALL_SPEC='.[full,timing]'
if [[ "${1:-}" == "--minimal" ]]; then
    INSTALL_SPEC='.'
    shift
fi

echo "=============================="
echo " lrc-tools setup"
echo "=============================="
echo "Installing editable package into your user environment..."
echo "Dependency profile: ${INSTALL_SPEC}"
echo

printf 'Running: %s\n\n' "python3 -m pip install --user -e ${INSTALL_SPEC}"
python3 -m pip install --user -e "${INSTALL_SPEC}" "$@"

echo
echo "Done. Available commands:"
echo "  - lrc-tools"
echo "  - lt"
echo "  - lrc-fetch"
echo "  - lrc-processor"
echo "  - lrc-vis"
echo
echo "If ~/.local/bin is not on your PATH, add:"
echo '  export PATH="$HOME/.local/bin:$PATH"'
