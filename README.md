# lrc-tools

```
  _      ____   ___    _____           _
 | |    |___ \ / _ \  |_   _|_ _  ___| |_
 | |      __) | | | |   | |/ _` |/ _ \ __|
 | |___  / __/| |_| |   | | (_| |  __/ |_
 |_____|_____| \___/    |_|\__,_|\___|\__|
```

Terminal synced lyrics toolkit — fetch, process, and visualize `.lrc` lyrics from your terminal.

[![CI](https://img.shields.io/github/actions/workflow/status/RicknotDev/lrc-tools/ci.yml?branch=main&label=CI)](https://github.com/RicknotDev/lrc-tools/actions)
[![Lint](https://img.shields.io/github/actions/workflow/status/RicknotDev/lrc-tools/lint.yml?branch=main&label=Lint)](https://github.com/RicknotDev/lrc-tools/actions)
[![PyPI](https://img.shields.io/pypi/v/lrc-tools)](https://pypi.org/project/lrc-tools/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20windows-informational)](#)

## What is this?

Three operations from the terminal:

1. **Fetch** synced lyrics from [LRCLIB](https://lrclib.net) for your music library
2. **Process** `.lrc` into word-level `.wlrc` with phrase splitting and onset detection
3. **Visualize** lyrics in real time while music is playing (MPRIS / mpv / ffplay)

New? Run `lrc-tools`, pick your music folder, fetch → process → enjoy.

## Quick install

```bash
pip install --user lrc-tools
# Or with extras:
pip install --user "lrc-tools[full]"   # +mutagen +syncedlyrics +textual
```

Or download a binary from [Releases](https://github.com/RicknotDev/lrc-tools/releases).

**System requirements:** Python 3.12+, `ffmpeg`/`ffprobe`, `playerctl` (Linux only).

## Commands

| Command | What it does |
|---------|-------------|
| `lrc-tools` / `lt` | Interactive TUI (or simple menu if Textual is missing) |
| `lrc-fetch` | Batch download `.lrc` lyrics from LRCLIB |
| `lrc-processor` | Split phrases, convert `.lrc` → `.wlrc` |
| `lrc-vis` | Real-time lyric visualizer in the terminal |

### CLI examples

```bash
# Fetch lyrics for all songs in ~/Music
lrc-fetch --audio-dir ~/Music --output-dir ~/.local/share/lrc-tools/lyrics/raw

# Process to word-level with custom split settings
lrc-processor --lrc-dir ./raw --audio-dir ./music --output-dir ./out --wlrc \
  --max-phrase-duration 3.0 --max-words 10

# Visualize with auto-match from media player
lrc-vis --lrc-dir ~/.local/share/lrc-tools/lyrics/processed --wlrc

# Validate an LRC file
python3 -c "from lrc_tools.parser import validate_lrc; print(validate_lrc('file.lrc'))"

# Export LRC to SRT subtitles
python3 -c "from lrc_tools.exporters import export_srt; export_srt('file.lrc', 'file.srt')"
```

See `--help` on any command for full options.

## Default paths

| What | Path |
|------|------|
| Raw lyrics | `~/.local/share/lrc-tools/lyrics/raw` |
| Processed lyrics | `~/.local/share/lrc-tools/lyrics/processed` |
| Config | `~/.config/lrc-tools/config.yaml` |

On macOS: `~/Library/Application Support/` and `~/Library/Preferences/`.  
On Windows: `%LOCALAPPDATA%` and `%APPDATA%`.

## Workflow

```
Audio files  ──→  lrc-fetch  ──→  .lrc (raw)  ──→  lrc-processor  ──→  .wlrc  ──→  lrc-vis
```

Or from the TUI: `lrc-tools` → Configure paths → Fetch → Process → Visualize.

## Features

| Feature | Status |
|---------|--------|
| Fetch lyrics from LRCLIB | ✅ |
| syncedlyrics fallback provider | ✅ |
| Phrase splitting (commas, duration, word count) | ✅ |
| Word-level WLRC format | ✅ |
| Onset detection via librosa | ✅ |
| Real-time visualizer (playerctl / mpv / ffplay) | ✅ |
| Textual TUI | ✅ |
| CLI with rich progress bars and colors | ✅ |
| Cross-platform (Linux / macOS / Windows) | ✅ |
| LRC validation and repair | ✅ |
| Timestamp offset (shift all timestamps) | ✅ |
| Merge / split LRC files | ✅ |
| Export to SRT subtitles | ✅ |
| Export/import JSON | ✅ |
| Dry-run mode | ✅ |
| Auto-backup before overwrite | ✅ |
| PyInstaller binaries | ✅ |
| Custom ASCII fonts | ✅ |

## Docs

- [Configuration](docs/configuration.md)
- [File formats](docs/file-formats.md)
- [Troubleshooting](docs/troubleshooting.md)
- [API reference](docs/api.md)

## Development

```bash
git clone https://github.com/RicknotDev/lrc-tools
cd lrc-tools
pip install -e ".[full]"
python -m unittest discover -s tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
