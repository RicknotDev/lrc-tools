# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] — 2026-06-22

### Added
- `parser.py`: `validate_lrc()`, `repair_lrc()`, `offset_timestamps()`, `merge_lrc()`, `split_lrc()`, `parse_metadata()`
- `exporters.py`: export LRC to SRT (subtitles) and JSON
- `importers.py`: import SRT and JSON back to LRC
- `core.py`: `backup_file()` helper with auto-backup before overwrite in `save_lyrics()`
- CLI: `--dry-run` flag for `lrc-fetch`
- CLI: `rich` progress bars, colored output, elegant error handling (`rich.traceback`)
- CLI: `--help` with usage examples for all entry points
- TUI: refactored from 1002-line monolith to 8 screen files + 2 widget files
- Tests: 69 new tests (`test_parser`, `test_exporters`, `test_splitter`, `test_puller`, `test_cli`, `test_utils`)
- GitHub: lint workflow (ruff + mypy + bandit), issue/PR templates
- Community: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`

### Changed
- `rich>=13.0` promoted to base dependency
- `save_lyrics()` now creates `.bak` before overwriting existing files; skips backup if content unchanged
- Version bumped to 0.3.0

### Fixed
- `prompt_threads()`: `if default:` -> `if default is not None:` (broke `--search-threads 0`)
- `display.py` `render_block_text()`: non-ASCII characters (é, ñ, ü) now render as base letters
- `fonts.py`: added `FALLBACK_CHARS` map for accented character support
- `config.py`: guarded `import yaml` with try/except for missing PyYAML
- Cross-platform: 15 issues fixed across audio_player, player, display, install scripts, Makefile

## [0.2.0] — 2026-06-22

### Added
- Migrated to `src/lrc_tools/` layout
- Platform detection: `IS_LINUX`, `IS_MACOS`, `IS_WINDOWS` with XDG paths per OS
- `install.sh` (cross-platform bash), `install.ps1` (Windows PowerShell)
- `uninstall.sh` with config/data cleanup prompts
- `scripts/verify_install.py`, `scripts/build_binary.py` (PyInstaller)
- CI matrix: ubuntu/macos/windows × python 3.12/3.13
- Release workflow with sdist + PyInstaller binaries + PyPI publish

### Changed
- Heavy deps (librosa, textual, syncedlyrics, mutagen) moved to optional extras
- `--break-system-packages` conditional on PEP 668 detection
- Race condition fixes: `threading.Lock` on caches and `SyncData`

## [0.1.0] — 2026-06-?? (initial release)

### Added
- LRC fetching from LRCLIB
- LRC processing (phrase splitting, word-level conversion)
- LRC visualizer with terminal display
- Textual TUI
