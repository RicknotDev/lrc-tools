#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=============================="
echo " lrc-tools setup"
echo "=============================="
echo "Installing editable package into your user environment..."
echo

action_cmd=(python3 -m pip install --user -e "$SCRIPT_DIR")
printf 'Running: '
printf '%q ' "${action_cmd[@]}"
printf '\n\n'
"${action_cmd[@]}"

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
