#!/usr/bin/env bash
# lrc-tools cross-platform installer (Linux / macOS / WSL)
set -euo pipefail

REPO="https://github.com/RicknotDev/lrc-tools"
INSTALL_SPEC="${1:-.}"

echo "============================================"
echo " lrc-tools installer"
echo "============================================"

# Detect OS
OS="$(uname -s)"
case "$OS" in
  Linux)  PLATFORM="linux" ;;
  Darwin) PLATFORM="macos" ;;
  CYGWIN*|MINGW*|MSYS*) PLATFORM="windows"; echo "NOTE: On Windows, use install.ps1 (PowerShell) instead."; exit 0 ;;
  *)      echo "Unsupported OS: $OS"; echo "On Windows, use: powershell -ExecutionPolicy Bypass -File install.ps1"; exit 1 ;;
esac
echo "Platform: $PLATFORM"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 not found."
  echo "  Install Python 3.12+ from https://python.org"
  exit 1
fi

PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Python: $PYVER"

# Install pip if missing
python3 -m pip --version &>/dev/null || {
  echo "Installing pip..."
  curl -sS https://bootstrap.pypa.io/get-pip.py | python3
}

echo ""
echo "Installing lrc-tools..."
python3 -m pip install --user -e "$INSTALL_SPEC" 2>&1 || {
  echo ""
  echo "Retrying with --break-system-packages (Debian/Ubuntu)..."
  python3 -m pip install --user --break-system-packages -e "$INSTALL_SPEC"
}

echo ""
echo "Verifying installation..."
if python3 -c "from lrc_tools import __version__; print(__version__)" &>/dev/null; then
  VER=$(python3 -c "from lrc_tools import __version__; print(__version__)")
  echo "  ✓ lrc-tools v$VER installed"
else
  echo "  ✗ Installation failed"
  exit 1
fi

# Add ~/.local/bin to PATH reminder
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  echo ""
  echo "NOTE: Add ~/.local/bin to your PATH:"
  echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
  echo "  source ~/.bashrc"
fi

echo ""
echo "Available commands:"
echo "  lrc-tools       # Open the TUI"
echo "  lrc-fetch       # Download lyrics"
echo "  lrc-processor   # Process lyrics to word-level"
echo "  lrc-vis         # Launch visualizer"
echo ""
echo "Quick start: lrc-tools"
