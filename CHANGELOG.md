# Changelog

All notable changes to this project will be documented in this file.

## [0.6.0] — 2026-11-13

### Added
- TUI: **Revisar letras** screen (`c` / `5`) — validates every downloaded `.lrc`, explains each problem, and repairs duplicate/unsorted timestamps with a `.bak` backup; plain-text lyrics are flagged as not repairable
- TUI: full shortcut reference on `?` (was an 8-second toast)
- TUI: "Siguiente paso" hint in the status panel that guides you through folder → fetch → process → visualize
- TUI: task screens show the running phase and elapsed time; `c` cancels the running process and `Esc` asks before leaving a running task
- TUI song picker: `Enter` in the search box launches the first match, `↓` jumps into the list
- `tests/test_tui_improvements.py`: 18 tests (process runner, cancel, lyrics check/repair, help, small-terminal layout, next-step logic)

### Fixed
- TUI: the ASCII banner was garbled (it did not spell "lrc-tools") and took 8 rows; replaced by a one-line header with the version
- TUI: at 100×30 only 3 of 10 menu options were visible; items are now single-line and all fit in 80×24
- TUI: the status panel had no border/padding (CSS targeted a non-existent id)
- TUI: leaving a task with `Esc` left the child process running in the background; the "Ctrl+C cancela" hint actually quit the whole app
- TUI: child processes inherited the terminal's stdin (could hang the TUI waiting for input) and wrapped output at 80 columns
- Quick mode closed itself the instant it finished, so the log could not be read
- Install hints (`pip install "lrc-tools[...]"`) pointed at PyPI, where the package is not published; they now install the actual dependency

### Changed
- README and docs install from GitHub (`pip install "lrc-tools[full] @ git+https://github.com/RicknotDev/lrc-tools.git"`) instead of PyPI
- TUI menu labels are consistently in Spanish; menu numbers changed: 5 = Revisar letras, 6 = Descargar canciones, 7 = Rutas, 8 = Dependencias, 9 = Ajustes, 0 = Borrar letras
- `ConfirmDialog`: `Esc` now means "No"

## [0.5.0] — 2026-11-13

### Added
- Standalone binaries for **all four tools** (`lrc-tools`, `lrc-fetch`, `lrc-processor`, `lrc-vis`) on Linux, macOS (Apple Silicon) and Windows, attached to each GitHub Release
- `--version` flag on every CLI entry point
- LRC parsing now supports lines with several timestamps (`[00:10.00][00:50.00]Chorus`), timestamps without fractions (`[01:05]`) and minutes > 99
- Standard LRC tags `[offset:]`, `[au:]`, `[tool:]` and `[#:]` are recognised as metadata
- `tests/test_parser_edge.py`: 21 regression tests (BOM, multi-timestamps, rounding, CRLF SRT, malformed JSON, CLI `--version`/`--help`)

### Fixed
- **Release pipeline**: `scripts/build_binary.py` passed an invalid entry point to PyInstaller, so every release build failed and no binaries were ever published. It now generates real launchers, collects `rich`/`textual` data, and the workflow smoke-tests each binary before uploading
- Release workflow: PyPI publishing is skipped (instead of failing the job) when no `PYPI_TOKEN` secret is configured; sdist/wheel are now actually found for upload
- Files saved with a UTF-8 BOM (Windows Notepad, many editors) lost their first lyric line; `[ti:]` on the first line was ignored
- `format_timestamp()` / `offset_timestamps()` could produce invalid `[00:60.00]`; SRT export could produce `00:00:60,000`
- SRT import failed on multi-line subtitles in CRLF files; JSON import crashed on entries without a timestamp
- `split_lrc()` crashed with `n=0` and produced unbalanced chunks (last part carried the whole remainder)
- `lrc-fetch`: the download thread prompt used the *search* thread config value; it no longer blocks waiting for input when run non-interactively or with `-y`
- `lrc-processor`: explicit `0` values for `--min-phrase-duration` etc. were silently replaced by defaults; invalid values are now rejected
- `--help` output showed raw rich markup (`[bold]`, `[dim]`) in the examples section
- Crash tracebacks no longer dump every local variable (`show_locals`), which was noisy and could expose file paths/lyrics content
- Fallback menu (no Textual installed) now runs the tools through the current interpreter, so it works when the scripts dir is not on `PATH`

### Changed
- Ruff rule set pinned in `pyproject.toml` (`E, F, W, I, UP, B`) so new ruff releases cannot break CI; code modernised to PEP 585/604 annotations

## [0.4.0] — 2026-06-23

### Added
- macOS: visualizer auto-detects Music.app, Spotify and VLC via AppleScript (no playerctl needed)
- macOS: more music directory candidates (`~/Music/iTunes`, `~/Music/Music`, `~/Music/Spotify`)

### Fixed
- Windows: `install.ps1` adds the Python Scripts dir to the user `PATH`
- Windows: commands are looked up in every Python Scripts directory; spotdl missing no longer crashes
- Windows: stdout/stderr forced to UTF-8 to prevent `UnicodeEncodeError`

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
