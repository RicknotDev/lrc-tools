"""Shared logic for lrc-tools TUI and CLI helpers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import sysconfig
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform.startswith("darwin")
IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    _XDG_CONFIG = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    _XDG_DATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
elif IS_MACOS:
    _XDG_CONFIG = Path.home() / "Library" / "Preferences"
    _XDG_DATA = Path.home() / "Library" / "Application Support"
else:
    _XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    _XDG_DATA = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))

CONFIG_DIR = _XDG_CONFIG / "lrc-tools"
DATA_DIR = _XDG_DATA / "lrc-tools"
LYRICS_RAW = DATA_DIR / "lyrics" / "raw"
LYRICS_PROCESSED = DATA_DIR / "lyrics" / "processed"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
STATE_FILE = CONFIG_DIR / ".setup_done"
BIN_DIR = Path.home() / ".local" / "bin"

AUDIO_EXTENSIONS = {".mp3", ".flac", ".ogg", ".wav", ".m4a", ".opus", ".aac", ".wma"}
_COUNT_CACHE: dict[tuple[str, str], tuple[float, int]] = {}
_DEP_CACHE: tuple[float, list[Dependency]] | None = None
_COUNT_CACHE_TTL = 8.0
_DEP_CACHE_TTL = 30.0
_cache_lock = threading.Lock()

_PEP_668 = (
    hasattr(sysconfig, "get_default_scheme")
    and "deb_system" in sysconfig.get_default_scheme()
)
_PIP_EXTRA = ["--break-system-packages"] if _PEP_668 else []


def repo_root() -> Path | None:
    env = os.environ.get("LRC_TOOLS_REPO")
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "setup.sh").is_file():
            return p
    return None


@dataclass
class TrackEntry:
    path: Path
    label: str


@dataclass
class Dependency:
    label: str
    key: str
    present: bool
    critical: bool
    install_hint: str
    install_cmd: list[str] | None


@dataclass
class AppState:
    music_dir: Path
    lyrics_raw: Path = LYRICS_RAW
    lyrics_processed: Path = LYRICS_PROCESSED
    config: Path = CONFIG_FILE

    def to_dict(self) -> dict:
        return {
            "music_dir": str(self.music_dir),
            "lyrics_raw": str(self.lyrics_raw),
            "lyrics_processed": str(self.lyrics_processed),
            "config": str(self.config),
        }

    @classmethod
    def from_dict(cls, data: dict) -> AppState:
        return cls(
            music_dir=Path(data.get("music_dir", Path.home() / "Music")).expanduser(),
            lyrics_raw=Path(data.get("lyrics_raw", LYRICS_RAW)),
            lyrics_processed=Path(data.get("lyrics_processed", LYRICS_PROCESSED)),
            config=Path(data.get("config", CONFIG_FILE)),
        )


def load_state() -> AppState | None:
    if not STATE_FILE.is_file():
        return None
    try:
        return AppState.from_dict(json.loads(STATE_FILE.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError, TypeError):
        return None


def save_state(state: AppState) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def default_state() -> AppState:
    existing = load_state()
    if existing:
        return existing
    music = Path.home() / "Music"
    return AppState(music_dir=music)


def ensure_lyrics_dirs() -> None:
    LYRICS_RAW.mkdir(parents=True, exist_ok=True)
    LYRICS_PROCESSED.mkdir(parents=True, exist_ok=True)


def _cached_count(key: tuple[str, str], compute: Callable[[], int]) -> int:
    global _COUNT_CACHE
    now = time.monotonic()
    with _cache_lock:
        cached = _COUNT_CACHE.get(key)
        if cached and (now - cached[0]) < _COUNT_CACHE_TTL:
            return cached[1]
    value = compute()
    with _cache_lock:
        _COUNT_CACHE[key] = (now, value)
    return value


def count_audio(directory: Path) -> int:
    if not directory.is_dir():
        return 0

    def _compute() -> int:
        total = 0
        for _root, _dirs, files in os.walk(directory):
            for name in files:
                if Path(name).suffix.lower() in AUDIO_EXTENSIONS:
                    total += 1
        return total

    return _cached_count(("audio", str(directory.resolve())), _compute)


def count_files(directory: Path, pattern: str) -> int:
    if not directory.is_dir():
        return 0
    return _cached_count(
        (f"files:{pattern}", str(directory.resolve())),
        lambda: sum(1 for _ in directory.rglob(pattern)),
    )


def command_exists(name: str) -> bool:
    if shutil.which(name) is not None:
        return True
    if IS_WINDOWS:
        scripts_dir = Path(sysconfig.get_path("scripts"))
        if (scripts_dir / name).is_file() or (scripts_dir / f"{name}.exe").is_file():
            return True
        user_base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Python"
        for site in user_base.glob("*/Scripts"):
            if (site / name).is_file() or (site / f"{name}.exe").is_file():
                return True
    return False


def find_command(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    if IS_WINDOWS:
        scripts_dir = Path(sysconfig.get_path("scripts"))
        for candidate in [scripts_dir / name, scripts_dir / f"{name}.exe"]:
            if candidate.is_file():
                return str(candidate)
        user_base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Python"
        for site in user_base.glob("*/Scripts"):
            for candidate in [site / name, site / f"{name}.exe"]:
                if candidate.is_file():
                    return str(candidate)
    return name


def python_importable(module: str) -> bool:
    try:
        r = subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            capture_output=True,
            timeout=15,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def textual_available() -> bool:
    return python_importable("textual")


def scan_dependencies() -> list[Dependency]:
    global _DEP_CACHE

    now = time.monotonic()
    with _cache_lock:
        if _DEP_CACHE and (now - _DEP_CACHE[0]) < _DEP_CACHE_TTL:
            return list(_DEP_CACHE[1])

    spotdl_install_cmd = (
        ["pipx", "install", "spotdl"] if command_exists("pipx") else None
    )
    pip_cmd = [sys.executable, "-m", "pip", "install"] + _PIP_EXTRA

    if IS_LINUX:
        playerctl_install_hint = "sudo pacman -S playerctl  # or: brew install playerctl"
        playerctl_install_cmd = ["sudo", "pacman", "-S", "--needed", "playerctl"]
    elif IS_MACOS:
        playerctl_install_hint = "brew install playerctl"
        playerctl_install_cmd = ["brew", "install", "playerctl"]
    else:
        playerctl_install_hint = "Not available on Windows"
        playerctl_install_cmd = None

    if IS_WINDOWS:
        ffmpeg_install_hint = "choco install ffmpeg  # or: winget install ffmpeg"
        ffmpeg_install_cmd = ["choco", "install", "-y", "ffmpeg"]
    elif IS_MACOS:
        ffmpeg_install_hint = "brew install ffmpeg"
        ffmpeg_install_cmd = ["brew", "install", "ffmpeg"]
    else:
        ffmpeg_install_hint = "sudo pacman -S ffmpeg  # or: sudo apt install ffmpeg"
        ffmpeg_install_cmd = ["sudo", "pacman", "-S", "--needed", "ffmpeg"]

    if IS_WINDOWS:
        yaml_hint = "pip install PyYAML (included with lrc-tools)"
        yaml_cmd = pip_cmd + ["PyYAML"]
    elif IS_MACOS:
        yaml_hint = "pip install PyYAML (included with lrc-tools)"
        yaml_cmd = pip_cmd + ["PyYAML"]
    else:
        yaml_hint = "sudo pacman -S python-pyyaml"
        yaml_cmd = ["sudo", "pacman", "-S", "--needed", "python-pyyaml"]

    deps = [
        Dependency(
            "playerctl" if IS_LINUX else "playerctl (MPRIS)",
            "playerctl",
            command_exists("playerctl") if not IS_WINDOWS else False,
            IS_LINUX,
            playerctl_install_hint,
            playerctl_install_cmd,
        ),
        Dependency(
            "ffmpeg / ffprobe",
            "ffmpeg",
            command_exists("ffprobe"),
            True,
            ffmpeg_install_hint,
            ffmpeg_install_cmd,
        ),
        Dependency(
            "PyYAML",
            "yaml",
            python_importable("yaml"),
            True,
            yaml_hint,
            yaml_cmd,
        ),
        Dependency(
            "mutagen",
            "mutagen",
            python_importable("mutagen"),
            False,
            f"{' '.join(pip_cmd)} mutagen",
            pip_cmd + ["mutagen"],
        ),
        Dependency(
            "syncedlyrics",
            "syncedlyrics",
            python_importable("syncedlyrics"),
            False,
            f"{' '.join(pip_cmd)} syncedlyrics",
            pip_cmd + ["syncedlyrics"],
        ),
        Dependency(
            "librosa",
            "librosa",
            python_importable("librosa"),
            False,
            f"{' '.join(pip_cmd)} librosa",
            pip_cmd + ["librosa"],
        ),
        Dependency(
            "textual (TUI)",
            "textual",
            textual_available(),
            True,
            f"{' '.join(pip_cmd)} textual",
            pip_cmd + ["textual"],
        ),
        Dependency(
            "spotdl (descargador)",
            "spotdl",
            command_exists("spotdl"),
            False,
            "pipx install spotdl  # recomendado",
            spotdl_install_cmd,
        ),
    ]
    with _cache_lock:
        _DEP_CACHE = (now, deps)
    return list(deps)


def critical_deps_ok(*, include_tui: bool = False) -> bool:
    return all(
        d.present
        for d in scan_dependencies()
        if d.critical and (include_tui or d.key != "textual")
        and not (d.key == "playerctl" and not IS_LINUX)
    )


def tools_installed() -> bool:
    return (BIN_DIR / "lrc-fetch").is_file() or command_exists("lrc-fetch")


def lrc_tool_cmd(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    local = BIN_DIR / name
    if local.is_file():
        return str(local)
    raise FileNotFoundError(
        f"{name} no está instalado. Usá «Setup» o ejecutá setup.sh desde el repo."
    )


def config_yaml(use_onset: bool = False) -> str:
    onset = "true" if use_onset else "false"
    return f"""# lrc-tools
processor:
  max_phrase_duration: 2.5
  max_words_per_phrase: 8
  split_on_commas: true
  use_onset_detection: {onset}
  onset_blend_factor: 0.5

puller:
  search_threads: 4
  download_threads: 4
  preserve_structure: true
  prefer_synced: true
  overwrite: false

visualizer:
  default_font: block
  refresh_rate: 0.05
  word_display_time: 0.3
  clear_screen: true
"""


def ensure_config(use_onset: bool | None = None) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        onset = use_onset if use_onset is not None else python_importable("librosa")
        CONFIG_FILE.write_text(config_yaml(onset), encoding="utf-8")
    root = repo_root()
    if root:
        src = root / "custom_fonts.json"
        dst = CONFIG_DIR / "custom_fonts.json"
        if src.is_file() and not dst.exists():
            shutil.copy2(src, dst)


def run_setup_script(on_line: Callable[[str], None] | None = None) -> int:
    root = repo_root()
    if not root:
        raise FileNotFoundError("No se encontró setup.sh (definí LRC_TOOLS_REPO).")
    setup = root / "setup.sh"
    return run_command(["bash", str(setup)], on_line=on_line)


def run_command(
    cmd: list[str],
    *,
    stdin_text: str | None = None,
    on_line: Callable[[str], None] | None = None,
) -> int:
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if stdin_text else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except OSError as e:
        raise FileNotFoundError(f"Command not found: {cmd[0]}") from e

    if stdin_text and proc.stdin:
        proc.stdin.write(stdin_text)
        proc.stdin.close()

    assert proc.stdout is not None
    for line in proc.stdout:
        if on_line:
            on_line(line.rstrip("\n"))
    return proc.wait()


def iter_command(cmd: list[str], *, stdin_text: str | None = None) -> Iterator[str]:
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if stdin_text else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except OSError as e:
        raise FileNotFoundError(f"Command not found: {cmd[0]}") from e

    if stdin_text and proc.stdin:
        proc.stdin.write(stdin_text)
        proc.stdin.close()
    assert proc.stdout is not None
    for line in proc.stdout:
        yield line.rstrip("\n")
    proc.wait()


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def validate_music_dir(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "La ruta no existe"
    if not path.is_dir():
        return False, "No es un directorio"
    return True, "ok"


def download_music_dir() -> Path:
    path = Path.home() / "Music"
    path.mkdir(parents=True, exist_ok=True)
    return path


def spotdl_cmd(url: str) -> list[str]:
    clean_url = url.strip()
    if not clean_url:
        raise ValueError("Ingresá un link válido para descargar")
    target = download_music_dir()
    return [find_command("spotdl"), "download", clean_url, "--output", str(target)]


def music_dir_candidates() -> list[Path]:
    raw = [
        Path.home() / "Music",
        Path.home() / "Música",
        Path.home() / "music",
        Path.home() / "Music" / "iTunes",
        Path.home() / "Music" / "Music",
        Path.home() / "Music" / "Spotify",
        Path.home() / "Downloads",
    ]
    if IS_LINUX:
        raw.extend([Path("/mnt"), Path("/media") / os.environ.get("USER", "")])
    seen: set[Path] = set()
    out: list[Path] = []
    for p in raw:
        try:
            r = p.expanduser().resolve()
        except OSError:
            continue
        if r in seen:
            continue
        seen.add(r)
        if r.is_dir():
            out.append(r)
    return out


def list_subdirs(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    dirs = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    return sorted(dirs, key=lambda p: p.name.lower())


def config_summary() -> dict[str, str]:
    defaults = {
        "preserve_structure": "true",
        "search_threads": "4",
        "download_threads": "4",
        "use_onset_detection": "false",
        "default_font": "block",
    }
    if not CONFIG_FILE.is_file():
        return {**defaults, "_status": "sin archivo (se creará al guardar)"}

    try:
        import yaml

        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return {**defaults, "_status": "config.yaml presente (no se pudo leer)"}

    puller = data.get("puller") or {}
    processor = data.get("processor") or {}
    visualizer = data.get("visualizer") or {}
    return {
        "_status": "ok",
        "preserve_structure": str(puller.get("preserve_structure", True)).lower(),
        "search_threads": str(puller.get("search_threads", 4)),
        "download_threads": str(puller.get("download_threads", 4)),
        "use_onset_detection": str(processor.get("use_onset_detection", False)).lower(),
        "default_font": str(visualizer.get("default_font", "block")),
    }


def is_first_run() -> bool:
    return not STATE_FILE.is_file()


def fetch_cmd(state: AppState) -> list[str]:
    return [
        lrc_tool_cmd("lrc-fetch"),
        "--audio-dir",
        str(state.music_dir),
        "--output-dir",
        str(state.lyrics_raw),
        "--config",
        str(state.config),
        "--search-threads",
        "4",
        "--download-threads",
        "4",
        "-y",
    ]


def process_cmd(state: AppState) -> list[str]:
    return [
        lrc_tool_cmd("lrc-processor"),
        "--lrc-dir",
        str(state.lyrics_raw),
        "--audio-dir",
        str(state.music_dir),
        "--output-dir",
        str(state.lyrics_processed),
        "--config",
        str(state.config),
        "--wlrc",
    ]


def list_tracks(
    lyrics_dir: Path,
    *,
    extension: str = ".wlrc",
) -> list[TrackEntry]:
    if not lyrics_dir.is_dir():
        return []
    entries: list[TrackEntry] = []
    for path in sorted(lyrics_dir.rglob(f"*{extension}"), key=lambda p: str(p).lower()):
        try:
            label = str(path.relative_to(lyrics_dir))
        except ValueError:
            label = path.name
        entries.append(TrackEntry(path=path, label=label))
    return entries


def vis_cmd(
    state: AppState,
    lrc_file: Path | None = None,
    *,
    play_audio: bool | None = None,
) -> list[str]:
    cmd = [
        lrc_tool_cmd("lrc-vis"),
        "--lrc-dir",
        str(state.lyrics_processed),
        "--wlrc",
        "--config",
        str(state.config),
        "--audio-dir",
        str(state.music_dir),
    ]
    if lrc_file is not None:
        cmd.extend(["--lrc-file", str(lrc_file.resolve()), "--pin"])
        if play_audio is not False:
            cmd.append("--play")
    elif play_audio:
        cmd.append("--play")
    return cmd


def backup_file(path: Path, backup_dir: Optional[Path] = None) -> Optional[Path]:
    if not path.is_file():
        return None
    dst = backup_dir or path.parent
    dst.mkdir(parents=True, exist_ok=True)
    backup_path = dst / f"{path.name}.bak"
    shutil.copy2(path, backup_path)
    return backup_path


def delete_track(state: AppState, track_path: Path) -> bool:
    deleted_any = False

    if track_path.is_file():
        track_path.unlink()
        deleted_any = True

    try:
        rel = track_path.relative_to(state.lyrics_processed)
        lrc_path = state.lyrics_raw / rel.with_suffix(".lrc")
    except ValueError:
        lrc_path = state.lyrics_raw / track_path.with_suffix(".lrc").name

    if lrc_path.is_file():
        lrc_path.unlink()
        deleted_any = True

    return deleted_any


def delete_all_lyrics(state: AppState) -> tuple[int, int]:
    lrc_count = 0
    wlrc_count = 0

    if state.lyrics_raw.is_dir():
        for p in list(state.lyrics_raw.rglob("*.lrc")):
            p.unlink()
            lrc_count += 1

    if state.lyrics_processed.is_dir():
        for p in list(state.lyrics_processed.rglob("*.wlrc")):
            p.unlink()
            wlrc_count += 1

    return lrc_count, wlrc_count


def system_stats(state: AppState) -> dict[str, str | int | bool]:
    ensure_lyrics_dirs()
    return {
        "music_dir": str(state.music_dir),
        "audio": count_audio(state.music_dir),
        "lrc": count_files(state.lyrics_raw, "*.lrc"),
        "wlrc": count_files(state.lyrics_processed, "*.wlrc"),
        "tools": tools_installed(),
        "config": CONFIG_FILE.is_file(),
        "deps_ok": critical_deps_ok(include_tui=True),
    }


def sidebar_snapshot(state: AppState) -> dict[str, Any]:
    stats = system_stats(state)
    deps = scan_dependencies()
    return {
        "stats": stats,
        "missing": [d.label for d in deps if not d.present and d.critical],
    }
