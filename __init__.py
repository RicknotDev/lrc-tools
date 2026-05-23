"""
lrc-tools — terminal lyrics visualizer and LRC processing suite
"""

import importlib
import sys
from types import ModuleType

from . import (
    audio,
    config,
    fonts,
    parser,
    processor_main,
    processor_splitter,
    puller,
    visualizer_display,
    visualizer_main,
    visualizer_player,
)

__version__ = "0.1.0"


def print_missing_optional(
    package_name: str, install_hint: str, description: str | None = None
) -> None:
    message = f"✗ '{package_name}' is not installed"
    if description:
        message += f" — needed for {description}."
    print(message, file=sys.stderr)
    print(f"  Install it with: {install_hint}", file=sys.stderr)

    pacman_pkg = {
        "textual": "python-textual",
        "librosa": "python-librosa",
        "mutagen": "python-mutagen",
        "syncedlyrics": "python-syncedlyrics",
    }.get(package_name)
    if pacman_pkg:
        print(f"  Or: sudo pacman -S {pacman_pkg}", file=sys.stderr)


def check_optional(
    package_name: str, install_hint: str, description: str | None = None
) -> ModuleType | None:
    try:
        return importlib.import_module(package_name)
    except ImportError:
        print_missing_optional(package_name, install_hint, description)
        return None
