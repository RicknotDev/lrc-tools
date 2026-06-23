# lrc-tools

```
  _      ____   ___    _____           _
 | |    |___ \ / _ \  |_   _|_ _  ___| |_
 | |      __) | | | |   | |/ _` |/ _ \ __|
 | |___  / __/| |_| |   | | (_| |  __/ |_
 |_____|_____| \___/    |_|\__,_|\___|\__|
```

Fetch, process, and visualize synced lyrics (`.lrc`) from your terminal.

[![CI](https://img.shields.io/github/actions/workflow/status/RicknotDev/lrc-tools/ci.yml?branch=main&label=CI)](https://github.com/RicknotDev/lrc-tools/actions)
[![PyPI](https://img.shields.io/pypi/v/lrc-tools)](https://pypi.org/project/lrc-tools/)
[![Python](https://img.shields.io/pypi/pyversions/lrc-tools)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20windows-informational)](#)

---

## Try it now

```bash
pip install lrc-tools
lrc-tools
```

Pick your music folder in the TUI, fetch lyrics, process them, and see them in real time — all without leaving the terminal.

---

## What is this?

Three operations, one toolkit:

| Step | Tool | What it does |
|------|------|-------------|
| 1 | `lrc-fetch` | Batch-download synced `.lrc` lyrics from [LRCLIB](https://lrclib.net) for your music library |
| 2 | `lrc-processor` | Convert `.lrc` to word-level `.wlrc` — split phrases, detect onsets, adjust timing |
| 3 | `lrc-vis` | Real-time lyric visualizer while music plays (MPRIS / mpv / ffplay) |

Everything is also available through the interactive TUI: `lrc-tools` opens a menu where you configure paths, fetch, process, and visualize without typing commands.

---

## Installation

### Requirements

- **Python 3.12+**
- **ffmpeg / ffprobe** (all platforms — used for audio analysis and playback)
- **playerctl** (Linux only — used for MPRIS media player integration)

### pip (Linux / macOS / Windows)

```bash
pip install lrc-tools

# With optional heavy deps (mutagen, librosa, textual):
pip install "lrc-tools[full]"
```

> Windows: works best in PowerShell or Windows Terminal. For best experience install `ffmpeg` via `winget install ffmpeg`.
>
> **Note:** If `lrc-tools` commands are not found after `pip install --user`, the Python `Scripts` directory is not in your PATH. The install script (`install.ps1`) adds it automatically. Otherwise run:
> ```powershell
> $scripts = python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
> $env:Path += ";$scripts"
> [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User") + ";$scripts", "User")
> ```
> Then restart your terminal.

### Binary release

Download a standalone executable from the [Releases page](https://github.com/RicknotDev/lrc-tools/releases) — no Python needed.

### Linux — install script

```bash
curl -fsSL https://raw.githubusercontent.com/RicknotDev/lrc-tools/main/install.sh | bash
```

### Windows — install script

```powershell
iwr -Uri https://raw.githubusercontent.com/RicknotDev/lrc-tools/main/install.ps1 | iex
```

---

## Commands

| Command | Entry point | What it does |
|---------|-------------|-------------|
| `lrc-tools` | `lrc_tools.cli.tui:main` | Interactive TUI (rich menu if Textual missing) |
| `lt` | same | Alias for `lrc-tools` |
| `lrc-fetch` | `lrc_tools.cli.fetch:main` | Batch-download `.lrc` from LRCLIB |
| `lrc-processor` | `lrc_tools.cli.process:main` | Split phrases, generate word-level `.wlrc` |
| `lrc-vis` | `lrc_tools.cli.vis:main` | Real-time visualizer in the terminal |

All commands accept `--help` for full options.

### `lrc-fetch`

```
usage: lrc-fetch --audio-dir DIR --output-dir DIR [options]

Options:
  --audio-dir DIR          Music folder to scan for audio files
  --output-dir DIR         Where to save .lrc files
  --search-threads N       Parallel search queries (default: cpu count)
  --download-threads N     Parallel download workers (default: cpu count)
  --overwrite              Overwrite existing .lrc files
  --no-preserve-structure  Flatten output (don't mirror audio-dir structure)
  --dry-run                Show what would be fetched without downloading
```

### `lrc-processor`

```
usage: lrc-processor --lrc-dir DIR --output-dir DIR [options]

Options:
  --lrc-dir DIR                Folder with .lrc files
  --audio-dir DIR              Audio files for onset detection
  --output-dir DIR             Output folder for processed files
  --wlrc                       Generate word-level .wlrc
  --overwrite                  Overwrite existing files
  --no-require-audio           Skip files without matching audio
  --max-phrase-duration SEC    Maximum seconds per phrase
  --min-phrase-duration SEC    Minimum seconds per phrase
  --max-words N                Max words per phrase before splitting
```

### `lrc-vis`

```
usage: lrc-vis --lrc-dir DIR [options]

Options:
  --lrc-dir DIR          Folder with .lrc/.wlrc files
  --audio-dir DIR        Auto-select matching track
  --wlrc                 Use word-level rendering
  --font FONT            Font name (block / compact)
  --custom-fonts DIR     Custom font directory
  --refresh-rate SEC     Visualizer refresh interval
```

---

## Examples

### 1. Fetch lyrics for your whole music library

```bash
lrc-fetch --audio-dir ~/Music --output-dir ~/lyrics/raw
```

### 2. Fetch with dry-run first

```bash
lrc-fetch --audio-dir ~/Music --output-dir ~/lyrics/raw --dry-run
```

### 3. Convert raw lyrics to word-level (with onset detection)

```bash
lrc-processor --lrc-dir ~/lyrics/raw --audio-dir ~/Music --output-dir ~/lyrics/processed --wlrc
```

### 4. Visualize while a song plays

```bash
# Start playing any song in your media player (Spotify, mpv, VLC…)
lrc-vis --lrc-dir ~/lyrics/processed --wlrc
```

### 5. Validate and repair a damaged LRC file

```bash
python3 -c "
from lrc_tools.parser import validate_lrc, repair_lrc
import sys
errors = validate_lrc('broken.lrc')
if errors:
    repair_lrc('broken.lrc', 'fixed.lrc')
    print('Repaired', len(errors), 'errors')
"
```

### 6. Export to SRT subtitles

```bash
python3 -c "from lrc_tools.exporters import export_srt; export_srt('song.lrc', 'song.srt')"
```

### 7. Shift all timestamps by +2 seconds

```bash
python3 -c "from lrc_tools.parser import offset_timestamps; offset_timestamps('song.lrc', 'shifted.lrc', 2.0)"
```

---

## Default paths

| What | Linux | macOS | Windows |
|------|-------|-------|---------|
| Raw lyrics | `~/.local/share/lrc-tools/lyrics/raw` | `~/Library/Application Support/lrc-tools/lyrics/raw` | `%LOCALAPPDATA%\lrc-tools\lyrics\raw` |
| Processed lyrics | `~/.local/share/lrc-tools/lyrics/processed` | `~/Library/Application Support/lrc-tools/lyrics/processed` | `%LOCALAPPDATA%\lrc-tools\lyrics\processed` |
| Config | `~/.config/lrc-tools/config.yaml` | `~/Library/Preferences/lrc-tools/config.yaml` | `%APPDATA%\lrc-tools\config.yaml` |

---

## Workflow

```
Audio files  ──→  lrc-fetch  ──→  .lrc (raw)  ──→  lrc-processor  ──→  .wlrc  ──→  lrc-vis
```

Or from the TUI: `lrc-tools` → Configure paths → Fetch → Process → Visualize.

---

## Features

| Area | Feature |
|------|---------|
| Fetch | LRCLIB provider, syncedlyrics fallback, parallel search/download, dry-run |
| Process | Phrase splitting (comma, duration, word count), word-level WLRC, onset detection |
| Visualize | Real-time display, playerctl/mpv/ffplay backends, custom ASCII fonts |
| Formats | LRC, WLRC, SRT export, JSON export/import |
| Tools | LRC validation, repair, timestamp offset, merge, split, auto-backup |
| Platform | Linux, macOS, Windows — same CLI everywhere |
| UI | Interactive TUI (textual if available, rich fallback), progress bars, colored output |

---

## Known problems & limitations

| Problem | Notes |
|---------|-------|
| **LRCLIB API rate limits** | Too many requests may return 429. Reduce `--search-threads`. |
| **syncedlyrics provider** | May return unsynced lyrics. Always check output. |
| **mpv on Windows** | IPC via `AF_UNIX` is not supported. Falls back to ffplay. |
| **playerctl** | Linux-only. On macOS/Windows visualizer uses mpv/ffplay directly. |
| **ffplay position drift** | Position is estimated via monotonic time, not actual playback position. |
| **Large libraries** | Fetching 1000+ files may take several minutes. Use `--dry-run` first. |

---

## API

lrc-tools is also usable as a Python library:

```python
from lrc_tools.parser import validate_lrc, repair_lrc, offset_timestamps, merge_lrc
from lrc_tools.exporters import export_srt, export_json
from lrc_tools.importers import import_srt, import_json
from lrc_tools.splitter import split_lrc
from lrc_tools.puller import save_lyrics
```

Full API reference at [docs/api.md](docs/api.md).

---

## Development

```bash
git clone https://github.com/RicknotDev/lrc-tools
cd lrc-tools
pip install -e ".[full]"
python -m unittest discover -s tests
```

91 tests covering parser, exporters, splitter, puller, CLI, and utilities.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Docs

- [Configuration](docs/configuration.md)
- [File formats](docs/file-formats.md)
- [Troubleshooting](docs/troubleshooting.md)
- [API reference](docs/api.md)

---

## License

MIT
