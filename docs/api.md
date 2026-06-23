# API Reference

This document lists the public API exported by `lrc-tools`.

## `lrc_tools` package

```python
from lrc_tools import __version__, check_optional, print_missing_optional
```

- `__version__` — current version string
- `check_optional(package, install_hint, description)` — try to import, print hint on failure
- `print_missing_optional(package, install_hint, description)` — print install hint to stderr

## `lrc_tools.core` — shared logic

```python
from lrc_tools.core import (
    AppState, Dependency, TrackEntry,
    load_state, save_state, default_state,
    ensure_lyrics_dirs, ensure_config,
    count_audio, count_files,
    scan_dependencies, critical_deps_ok,
    system_stats, sidebar_snapshot,
    list_tracks, list_subdirs,
    fetch_cmd, process_cmd, vis_cmd, spotdl_cmd,
    delete_track, delete_all_lyrics,
    backup_file,
    CONFIG_DIR, DATA_DIR, LYRICS_RAW, LYRICS_PROCESSED,
    IS_LINUX, IS_MACOS, IS_WINDOWS,
)
```

Platform detection, path management, dependency scanning, state persistence, and command builders.

## `lrc_tools.parser` — LRC parsing and validation

```python
from lrc_tools.parser import (
    parse_lrc, parse_lrc_simple, parse_metadata,
    format_timestamp, write_lrc,
    validate_lrc, repair_lrc, offset_timestamps,
    merge_lrc, split_lrc,
)
```

- `parse_lrc(path)` → `List[Dict]` — sorted list of `{timestamp, text}`
- `parse_lrc_simple(path)` → `List[Tuple[float, str]]`
- `parse_metadata(path)` → `Dict[str, str]` — extracts `[ti:]`, `[ar:]`, etc.
- `format_timestamp(seconds)` → `[MM:SS.xx]`
- `write_lrc(path, lines, metadata, header_comments)` — writes LRC file
- `validate_lrc(path)` → `List[str]` — returns list of issues (empty = valid)
- `repair_lrc(path, output_path)` → `int` — removes duplicates, returns count fixed
- `offset_timestamps(path, delta, output_path)` → `Path` — shifts all timestamps
- `merge_lrc(paths, output_path)` → `int` — merges multiple files, returns total lines
- `split_lrc(path, n, output_dir)` → `List[Path]` — splits into N parts

## `lrc_tools.exporters` — format export

```python
from lrc_tools.exporters import export_srt, export_json, export_lrc
```

- `export_srt(lrc_path, output_path)` → `Path` — export to SRT subtitles
- `export_json(lrc_path, output_path)` → `Path` — export to JSON
- `export_lrc(lrc_path, output_path, fmt)` → `Path` — generic: fmt=`"srt"` or `"json"`

## `lrc_tools.importers` — format import

```python
from lrc_tools.importers import import_srt, import_json, import_lrc
```

- `import_srt(srt_path)` → `List[Dict]` — import SRT to LRC dicts (pass to `write_lrc`)
- `import_json(json_path)` → `List[Dict]` — import JSON to LRC dicts
- `import_lrc(path, fmt)` → `List[Dict]` — generic: fmt=`"srt"` or `"json"`

## `lrc_tools.processor` — LRC processing

```python
from lrc_tools.processor import (
    process_lrc_file, process_long_phrases, phrases_to_words,
)
```

- `process_lrc_file(lrc_path, audio_dir, output_dir, ...)` → `bool` — full processing pipeline
- `process_long_phrases(lines, total_duration, ...)` → `List[Dict]` — split long phrases
- `phrases_to_words(phrases, audio_path, blend_factor)` → `List[Dict]` — convert to word-level

## `lrc_tools.splitter` — phrase splitting

```python
from lrc_tools.splitter import split_phrase_intelligently, find_split_point, find_all_split_points
```

- `split_phrase_intelligently(text, duration, start_time, ...)` → `List[Dict]`
- `find_split_point(words, prefer_index)` → `int`
- `find_all_split_points(text)` → `List[int]`

## `lrc_tools.puller` — lyric fetching

```python
from lrc_tools.puller import (
    search_song, search_lrclib, search_syncedlyrics,
    extract_metadata, extract_metadata_from_filename,
    resolve_output_path, save_lyrics,
    MUTAGEN_AVAILABLE, SYNCEDLYRICS_AVAILABLE,
)
```

## `lrc_tools.audio` — audio utilities

```python
from lrc_tools.audio import (
    get_audio_files, get_audio_duration,
    find_audio_for_lrc, find_lrc_for_audio,
    AUDIO_EXTENSIONS,
)
```

## `lrc_tools.config` — configuration dataclasses

```python
from lrc_tools.config import Config, ProcessorConfig, PullerConfig, VisualizerConfig
```

- `Config(config_file)` — loads from YAML/JSON
- `.processor`, `.puller`, `.visualizer` — config dataclass instances
- `.save(path)`, `.load(path)`, `.to_dict()`

## `lrc_tools.fonts` — ASCII fonts

```python
from lrc_tools.fonts import get_font, load_fonts_from_json, register_font
```

## `lrc_tools.visualizer` — terminal visualizer

```python
from lrc_tools.visualizer import run_visualizer
```

## `lrc_tools.utils` — utilities

```python
from lrc_tools.utils import count_syllables
```
