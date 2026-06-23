"""Media player integration using playerctl (MPRIS, Linux-only)."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

_HAVE_PLAYERCTL = os.name != "nt" and __import__("shutil").which("playerctl") is not None


def get_position() -> Optional[float]:
    if not _HAVE_PLAYERCTL:
        return None
    try:
        result = subprocess.run(
            ['playerctl', 'position'],
            capture_output=True, text=True, timeout=0.5
        )
        return float(result.stdout.strip()) if result.returncode == 0 else None
    except Exception:
        return None


def get_track() -> Optional[Tuple[str, str]]:
    if not _HAVE_PLAYERCTL:
        return None
    try:
        result = subprocess.run(
            ['playerctl', 'metadata', '--format', '{{artist}}|||{{title}}'],
            capture_output=True, text=True, timeout=0.5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split('|||')
            return (parts[0], parts[1]) if len(parts) == 2 else None
    except Exception:
        return None


def get_status() -> Optional[str]:
    if not _HAVE_PLAYERCTL:
        return None
    try:
        result = subprocess.run(
            ['playerctl', 'status'],
            capture_output=True, text=True, timeout=0.5
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def get_audio_file_info() -> Optional[Path]:
    if not _HAVE_PLAYERCTL:
        return None
    try:
        result = subprocess.run(
            ['playerctl', 'metadata', '--format', '{{xesam:url}}'],
            capture_output=True, text=True, timeout=0.5
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            if url.startswith('file://'):
                # Handle both file:///path (Unix) and file:///C:/path (Windows)
                return Path(url[7:])
            if url.startswith('file:'):
                return Path(url[5:])
    except Exception:
        pass
    return None


def is_paused() -> bool:
    status = get_status()
    return status == 'Paused' if status else False


def is_playing() -> bool:
    status = get_status()
    return status == 'Playing' if status else False
