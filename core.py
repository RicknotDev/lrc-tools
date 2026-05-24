"""
Shared logic for lrc-tools TUI and CLI helpers.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

# XDG (aligned with setup.sh)
XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
XDG_DATA = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
CONFIG_DIR = XDG_CONFIG / "lrc-tools"
DATA_DIR = XDG_DATA / "lrc-tools"
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
    label: str  # ruta relativa dentro del directorio de letras


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
    cached = _COUNT_CACHE.get(key)
    now = time.monotonic()
    if cached and (now - cached[0]) < _COUNT_CACHE_TTL:
        return cached[1]
    value = compute()
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
    return shutil.which(name) is not None


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
    if _DEP_CACHE and (now - _DEP_CACHE[0]) < _DEP_CACHE_TTL:
        return list(_DEP_CACHE[1])

    spotdl_install_cmd = (
        ["pipx", "install", "spotdl"] if command_exists("pipx") else None
    )
    deps = [
        Dependency(
            "playerctl",
            "playerctl",
            command_exists("playerctl"),
            True,
            "sudo pacman -S playerctl",
            ["sudo", "pacman", "-S", "--needed", "playerctl"],
        ),
        Dependency(
            "ffmpeg / ffprobe",
            "ffmpeg",
            command_exists("ffprobe"),
            True,
            "sudo pacman -S ffmpeg",
            ["sudo", "pacman", "-S", "--needed", "ffmpeg"],
        ),
        Dependency(
            "PyYAML",
            "yaml",
            python_importable("yaml"),
            True,
            "sudo pacman -S python-pyyaml",
            ["sudo", "pacman", "-S", "--needed", "python-pyyaml"],
        ),
        Dependency(
            "mutagen",
            "mutagen",
            python_importable("mutagen"),
            False,
            "sudo pacman -S python-mutagen",
            ["sudo", "pacman", "-S", "--needed", "python-mutagen"],
        ),
        Dependency(
            "syncedlyrics",
            "syncedlyrics",
            python_importable("syncedlyrics"),
            False,
            f"{sys.executable} -m pip install syncedlyrics --break-system-packages",
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "syncedlyrics",
                "--break-system-packages",
            ],
        ),
        Dependency(
            "librosa (opcional)",
            "librosa",
            python_importable("librosa"),
            False,
            f"{sys.executable} -m pip install librosa --break-system-packages",
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "librosa",
                "--break-system-packages",
            ],
        ),
        Dependency(
            "textual (TUI)",
            "textual",
            textual_available(),
            True,
            f"{sys.executable} -m pip install textual --break-system-packages",
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "textual",
                "--break-system-packages",
            ],
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
    _DEP_CACHE = (now, deps)
    return list(deps)


def critical_deps_ok(*, include_tui: bool = False) -> bool:
    return all(
        d.present
        for d in scan_dependencies()
        if d.critical and (include_tui or d.key != "textual")
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
        f"«{name}» no está instalado. Usá «Setup» o ejecutá setup.sh desde el repo."
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
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if stdin_text else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if stdin_text and proc.stdin:
        proc.stdin.write(stdin_text)
        proc.stdin.close()

    assert proc.stdout is not None
    for line in proc.stdout:
        if on_line:
            on_line(line.rstrip("\n"))
    return proc.wait()


def iter_command(cmd: list[str], *, stdin_text: str | None = None) -> Iterator[str]:
    """Yield stdout lines; call `.returncode` on the iterator after exhaustion — use run_command for code."""
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if stdin_text else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
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
    return ["spotdl", "download", clean_url, "--output", str(target)]


def music_dir_candidates() -> list[Path]:
    """Common music folder locations for the directory picker."""
    raw = [
        Path.home() / "Music",
        Path.home() / "Música",
        Path.home() / "music",
        Path("/mnt"),
        Path("/media") / os.environ.get("USER", ""),
        Path.home() / "Downloads",
    ]
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
    """Sorted subdirectories for browsing (excludes hidden)."""
    if not path.is_dir():
        return []
    dirs = [p for p in path.iterdir() if p.is_dir() and not p.name.startswith(".")]
    return sorted(dirs, key=lambda p: p.name.lower())


def config_summary() -> dict[str, str]:
    """Human-readable config values for the TUI settings screen."""
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
    """All lyric files under lyrics_dir (recursive), sorted for the song picker."""
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
