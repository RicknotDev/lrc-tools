# Configuration Reference

This document describes the `config.yaml` file used by `lrc-tools`.

## Location

- Default path: `~/.config/lrc-tools/config.yaml`
- XDG override: `XDG_CONFIG_HOME/lrc-tools/config.yaml`

## Top-level sections

- `processor`
- `puller`
- `visualizer`

## `processor`

### `max_phrase_duration`
Maximum duration for a phrase before it is split.

### `min_phrase_duration`
Minimum phrase duration to keep during processing.

### `max_words_per_phrase`
Maximum words allowed in a phrase before splitting.

### `split_on_commas`
If `true`, long phrases may be split at commas.

### `use_onset_detection`
If `true`, `librosa` is used for more detailed word timing.

### `onset_blend_factor`
Controls how strongly onset detection influences the generated timing.

## `puller`

### `search_threads`
Number of concurrent search workers.

### `download_threads`
Number of concurrent download workers.

### `request_delay`
Delay between network requests per worker.

### `max_retries`
Retry count for API/network failures.

### `retry_backoff`
Backoff multiplier applied between retries.

### `prefer_synced`
Prefer synced lyrics when the provider offers both synced and plain text.

### `preserve_structure`
Mirror the music library directory structure inside the lyrics output directory.

### `overwrite`
Overwrite existing lyric files.

## `visualizer`

### `default_font`
Default ASCII font name.

### `refresh_rate`
UI refresh interval in seconds.

### `word_display_time`
How long each word remains highlighted.

### `transition_style`
Visual transition mode between lyric updates.

### `colors_enabled`
Enable ANSI color output when supported.

### `clear_screen`
Clear the terminal between refreshes.

## Example

```/dev/null/config.yaml#L1-20
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
```
