"""Entry point for lrc-tools TUI (installed as lrc_tools.tui_main)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    from optional_deps import check_optional
except ImportError:
    try:
        from lrc_tools.optional_deps import check_optional
    except ImportError:
        check_optional = None


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
    textual = None
    if check_optional is not None:
        textual = check_optional(
            "textual",
            'python3 -m pip install --user "lrc-tools[full]"',
            "the TUI interface",
        )

    if textual is None:
        return _simple_menu()

    try:
        from lrc_tools.tui.app import main as tui_main
    except ImportError:
        from tui.app import main as tui_main
    return tui_main() or 0


if __name__ == "__main__":
    sys.exit(main())
