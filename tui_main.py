"""Entry point for lrc-tools TUI."""

from __future__ import annotations

import importlib
import subprocess
import sys


def _simple_menu() -> int:
    print("\n== lrc-tools ==")
    print("1) Launch interactive TUI")
    print("2) Run lrc-fetch")
    print("3) Run lrc-processor")
    print("4) Run lrc-vis")
    print("5) Exit")

    while True:
        choice = input("Select an option [1-5]: ").strip()
        if choice == "1":
            print("Textual is not installed, so the graphical TUI is unavailable.")
            print('Install it with: python3 -m pip install --user "lrc-tools[full]"')
            print("Or: sudo pacman -S python-textual")
            return 1
        if choice == "2":
            return subprocess.call(["lrc-fetch", "--help"])
        if choice == "3":
            return subprocess.call(["lrc-processor", "--help"])
        if choice == "4":
            return subprocess.call(["lrc-vis", "--help"])
        if choice == "5":
            return 0
        print("Invalid option.")


def main() -> int:
    try:
        importlib.import_module("textual")
    except ImportError:
        return _simple_menu()

    from tui.app import main as tui_main

    return tui_main() or 0


if __name__ == "__main__":
    sys.exit(main())
