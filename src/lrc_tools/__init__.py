"""lrc-tools — terminal lyrics visualizer and LRC processing suite."""

from __future__ import annotations

import importlib
import io
import os
import sys
from types import ModuleType

__version__ = "0.4.0"

if os.name == "nt" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True,
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True,
        )
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
    _IS_MACOS = sys.platform == "darwin"
    _IS_LINUX = sys.platform.startswith("linux")
    pkg_map = {
        "textual": "python-textual",
        "librosa": "python-librosa",
        "mutagen": "python-mutagen",
        "syncedlyrics": "python-syncedlyrics",
    }
    pkg = pkg_map.get(package_name)
    if pkg:
        if _IS_MACOS:
            print(f"  Or: brew install {package_name}", file=sys.stderr)
        elif _IS_LINUX:
            print(f"  Or: sudo pacman -S {pkg}", file=sys.stderr)


def check_optional(
    package_name: str, install_hint: str, description: str | None = None
) -> ModuleType | None:
    try:
        return importlib.import_module(package_name)
    except ImportError:
        print_missing_optional(package_name, install_hint, description)
        return None
