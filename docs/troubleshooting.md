# Troubleshooting

Common issues and fixes for `lrc-tools`.

## `playerctl` not found

### Symptom
The visualizer cannot detect the active player.

### Fix
- Install `playerctl`
- On Arch: `sudo pacman -S playerctl`
- Verify with `playerctl status`

## `ffprobe` not found

### Symptom
The processor cannot read audio duration.

### Fix
- Install `ffmpeg`
- On Arch: `sudo pacman -S ffmpeg`

## `textual` is not installed

### Symptom
The TUI does not launch.

### Fix
Install the full optional dependency set:

- `python3 -m pip install --user "lrc-tools[full]"`
- Or: `sudo pacman -S python-textual`

If Textual is missing, `lrc-tools` falls back to a simple terminal menu.

## `librosa` is not installed

### Symptom
Word-level onset detection is unavailable.

### Fix
- `python3 -m pip install --user "lrc-tools[timing]"`
- Or: `sudo pacman -S python-librosa`

The processor will fall back to evenly distributed timestamps.

## No lyrics match found

### Symptom
`lrc-fetch` scans files but downloads few or no lyrics.

### Things to check
- Embedded metadata tags are present
- Filenames follow `Artist - Title`
- The song exists in LRCLIB or fallback providers
- Your network connection is working

## Visualizer shows nothing

### Things to check
- The selected lyrics directory contains `.wlrc` files
- The current player exposes MPRIS metadata
- The filename stem matches the audio track
- You passed `--wlrc` when using word-level output

## Command not found after install

### Fix
Add `~/.local/bin` to your shell `PATH`.

Example:

```/dev/null/shell.sh#L1-1
export PATH="$HOME/.local/bin:$PATH"
```
