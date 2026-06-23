"""lrc-tools — terminal lyrics visualizer and LRC processing suite."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

__version__ = "0.3.0"
__all__ = [
    "__version__", "check_optional", "print_missing_optional",
    "AppState", "Dependency", "TrackEntry",
    "parse_lrc", "parse_lrc_simple", "write_lrc", "format_timestamp",
    "parse_metadata", "validate_lrc", "repair_lrc", "offset_timestamps",
    "merge_lrc", "split_lrc",
    "get_audio_duration", "find_audio_for_lrc", "find_lrc_for_audio", "get_audio_files",
    "export_srt", "export_json", "import_srt", "import_json",
    "backup_file",
]


def print_missing_optional(
    package_name: str, install_hint: str, description: str | None = None
) -> None:
    message = f"'{
        package_name}' is not installed"
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
