# Configuration Reference

This document describes the `config.yaml` file used by `lrc-tools`.

## Location

- Default path: `~/.config/lrc-tools/config.yaml` (Linux)
- macOS: `~/Library/Preferences/lrc-tools/config.yaml`
- Windows: `%APPDATA%/lrc-tools/config.yaml`
- Override: `--config /path/to/config.yaml`

## Example

```yaml
processor:
  max_phrase_duration: 2.5
  min_phrase_duration: 0.3
  max_words_per_phrase: 8
  split_on_commas: true
  use_onset_detection: false
  onset_blend_factor: 0.5

puller:
  search_threads: 5
  download_threads: 5
  request_delay: 0.05
  max_retries: 3
  retry_backoff: 0.5
  prefer_synced: true
  preserve_structure: true
  overwrite: false

visualizer:
  default_font: block
  refresh_rate: 0.05
  word_display_time: 0.3
  transition_style: instant
  colors_enabled: true
  clear_screen: true
```

## Sections

### `processor` — LRC processing options

| Key | Default | Description |
|-----|---------|-------------|
| `max_phrase_duration` | `2.5` | Max seconds per phrase before splitting |
| `min_phrase_duration` | `0.3` | Phrases shorter than this are skipped |
| `max_words_per_phrase` | `8` | Max words per phrase before splitting |
| `split_on_commas` | `true` | Split phrases at commas |
| `use_onset_detection` | `false` | Use librosa for word-level timing |
| `onset_blend_factor` | `0.5` | Blend between even distribution and onset detection (0=even, 1=onsets) |

### `puller` — Lyric fetching options

| Key | Default | Description |
|-----|---------|-------------|
| `search_threads` | `5` | Concurrent search requests |
| `download_threads` | `5` | Concurrent download requests |
| `request_delay` | `0.05` | Delay (seconds) between requests |
| `max_retries` | `3` | Retries on network failure |
| `retry_backoff` | `0.5` | Backoff multiplier between retries |
| `prefer_synced` | `true` | Prefer synced lyrics over plain text |
| `preserve_structure` | `true` | Mirror audio dir structure in output |
| `overwrite` | `false` | Overwrite existing `.lrc` files |

### `visualizer` — Display options

| Key | Default | Description |
|-----|---------|-------------|
| `default_font` | `block` | ASCII font name (block, compact, etc.) |
| `refresh_rate` | `0.05` | Terminal refresh interval (seconds) |
| `word_display_time` | `0.3` | How long each word stays highlighted |
| `transition_style` | `instant` | Animation style (instant, fade) |
| `colors_enabled` | `true` | Enable ANSI colors |
| `clear_screen` | `true` | Clear terminal between refreshes |

## Config file from CLI

You can pass `--config <path>` to any command to use a custom config file. Example:

```bash
lrc-fetch --audio-dir ~/Music --output-dir ./lyrics --config ~/configs/lrc-tools.yaml
```
