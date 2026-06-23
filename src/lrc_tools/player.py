"""Media player integration — playerctl (Linux), AppleScript (macOS)."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

_IS_MACOS = sys.platform == "darwin"
_IS_LINUX = sys.platform.startswith("linux")
_IS_WIN = os.name == "nt"

_HAVE_PLAYERCTL = _IS_LINUX and __import__("shutil").which("playerctl") is not None


def _run_osascript(script: str, timeout: float = 0.5) -> Optional[str]:
    if not _IS_MACOS:
        return None
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout,
        )
        output = result.stdout.strip()
        return output if result.returncode == 0 and output else None
    except Exception:
        return None


def _get_macos_player() -> Optional[str]:
    script = """
    if application "Spotify" is running then
        return "spotify"
    else if application "Music" is running then
        return "music"
    else if application "VLC" is running then
        return "vlc"
    end if
    """
    return _run_osascript(script)


def get_position() -> Optional[float]:
    if _HAVE_PLAYERCTL:
        return _get_position_playerctl()
    if _IS_MACOS:
        return _get_position_macos()
    return None


def get_track() -> Optional[Tuple[str, str]]:
    if _HAVE_PLAYERCTL:
        return _get_track_playerctl()
    if _IS_MACOS:
        return _get_track_macos()
    return None


def get_status() -> Optional[str]:
    if _HAVE_PLAYERCTL:
        return _get_status_playerctl()
    if _IS_MACOS:
        return _get_status_macos()
    return None


def get_audio_file_info() -> Optional[Path]:
    if _HAVE_PLAYERCTL:
        return _get_audio_file_playerctl()
    return None


def is_paused() -> bool:
    status = get_status()
    return status == "Paused" if status else False


def is_playing() -> bool:
    status = get_status()
    return status == "Playing" if status else False


# ── playerctl (Linux MPRIS) ───────────────────────────────────────────

def _get_position_playerctl() -> Optional[float]:
    try:
        result = subprocess.run(
            ["playerctl", "position"],
            capture_output=True, text=True, timeout=0.5,
        )
        return float(result.stdout.strip()) if result.returncode == 0 else None
    except Exception:
        return None


def _get_track_playerctl() -> Optional[Tuple[str, str]]:
    try:
        result = subprocess.run(
            ["playerctl", "metadata", "--format", "{{artist}}|||{{title}}"],
            capture_output=True, text=True, timeout=0.5,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split("|||")
            return (parts[0], parts[1]) if len(parts) == 2 else None
    except Exception:
        pass
    return None


def _get_status_playerctl() -> Optional[str]:
    try:
        result = subprocess.run(
            ["playerctl", "status"],
            capture_output=True, text=True, timeout=0.5,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def _get_audio_file_playerctl() -> Optional[Path]:
    try:
        result = subprocess.run(
            ["playerctl", "metadata", "--format", "{{xesam:url}}"],
            capture_output=True, text=True, timeout=0.5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            if url.startswith("file://"):
                return Path(url[7:])
            if url.startswith("file:"):
                return Path(url[5:])
    except Exception:
        pass
    return None


# ── AppleScript (macOS) ───────────────────────────────────────────────

_SPOTIFY_POS = '''
tell application "Spotify"
    set pos to player position
    set dur to duration of current track
    return (pos as integer) & "." & ((pos - (pos as integer)) * 1000 as integer) & "/" & dur
end tell
'''

_SPOTIFY_TRACK = '''
tell application "Spotify"
    set a to artist of current track
    set t to name of current track
    return a & "|||" & t
end tell
'''

_SPOTIFY_STATUS = '''
tell application "Spotify"
    if player state is playing then return "Playing"
    if player state is paused then return "Paused"
    return "Stopped"
end tell
'''

_MUSIC_POS = '''
tell application "Music"
    set pos to player position
    set dur to duration of current track
    return (pos as integer) & "." & ((pos - (pos as integer)) * 1000 as integer) & "/" & dur
end tell
'''

_MUSIC_TRACK = '''
tell application "Music"
    set a to artist of current track
    set t to name of current track
    return a & "|||" & t
end tell
'''

_MUSIC_STATUS = '''
tell application "Music"
    if player state is playing then return "Playing"
    if player state is paused then return "Paused"
    return "Stopped"
end tell
'''

_VLC_POS = '''
tell application "VLC"
    set pos to current time
    set dur to duration of current item
    return (pos as integer) & "." & ((pos - (pos as integer)) * 1000 as integer) & "/" & (dur as integer)
end tell
'''

_VLC_TRACK = '''
tell application "VLC"
    set t to name of current item
    return "|||" & t
end tell
'''

_VLC_STATUS = '''
tell application "VLC"
    if state is playing then return "Playing"
    if state is paused then return "Paused"
    return "Stopped"
end tell
'''


def _get_position_macos() -> Optional[float]:
    player = _get_macos_player()
    if not player:
        return None
    scripts = {"spotify": _SPOTIFY_POS, "music": _MUSIC_POS, "vlc": _VLC_POS}
    raw = _run_osascript(scripts.get(player, ""))
    if not raw or "/" not in raw:
        return None
    try:
        pos_str, _ = raw.split("/", 1)
        return float(pos_str)
    except (ValueError, TypeError):
        return None


def _get_track_macos() -> Optional[Tuple[str, str]]:
    player = _get_macos_player()
    if not player:
        return None
    scripts = {"spotify": _SPOTIFY_TRACK, "music": _MUSIC_TRACK, "vlc": _VLC_TRACK}
    raw = _run_osascript(scripts.get(player, ""))
    if not raw or "|||" not in raw:
        return None
    parts = raw.split("|||", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else None


def _get_status_macos() -> Optional[str]:
    player = _get_macos_player()
    if not player:
        return None
    scripts = {"spotify": _SPOTIFY_STATUS, "music": _MUSIC_STATUS, "vlc": _VLC_STATUS}
    return _run_osascript(scripts.get(player, ""))
