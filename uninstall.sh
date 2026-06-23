#!/usr/bin/env bash
# lrc-tools uninstaller
set -euo pipefail

echo "Uninstalling lrc-tools..."
python3 -m pip uninstall -y lrc-tools 2>/dev/null || true

# Remove config/data dirs (prompt)
case "$(uname -s)" in
  Darwin)
    CONFIG="${HOME}/Library/Preferences/lrc-tools"
    DATA="${HOME}/Library/Application Support/lrc-tools"
    ;;
  *)
    CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/lrc-tools"
    DATA="${XDG_DATA_HOME:-$HOME/.local/share}/lrc-tools"
    ;;
esac

echo ""
echo "Remove config directory? ($CONFIG)"
read -r -p "[y/N] " yn
if [[ "$yn" =~ ^[yY] ]]; then
    rm -rf "$CONFIG"
    echo "  Removed config"
fi

echo "Remove data directory? ($DATA)"
read -r -p "[y/N] " yn
if [[ "$yn" =~ ^[yY] ]]; then
    rm -rf "$DATA"
    echo "  Removed data"
fi

echo "Done."
