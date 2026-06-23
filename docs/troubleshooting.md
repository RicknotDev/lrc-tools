# Troubleshooting

Common issues and fixes for `lrc-tools`.

## `playerctl` not found

**Symptom:** The visualizer cannot detect the active player.

**Fix:**
- Linux: `sudo pacman -S playerctl` or `sudo apt install playerctl`
- macOS: `brew install playerctl`
- Windows: not available (use `lrc-vis --lrc-file song.wlrc --play --audio-dir ./music` instead)

Verify with `playerctl status`.

## `ffprobe` not found

**Symptom:** The processor cannot read audio duration.

**Fix:**
- Linux: `sudo pacman -S ffmpeg` or `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: `choco install ffmpeg` or `winget install ffmpeg`

## `textual` is not installed

**Symptom:** The TUI does not launch (falls back to simple terminal menu).

**Fix:**
```bash
pip install --user "lrc-tools[tui]"
# Or full:
pip install --user "lrc-tools[full]"
```

## `librosa` is not installed

**Symptom:** Word-level onset detection is unavailable. Processor falls back to evenly distributed timestamps.

**Fix:**
```bash
pip install --user "lrc-tools[timing]"
```

## No lyrics match found

**Symptom:** `lrc-fetch` scans files but downloads few or no lyrics.

**Check:**
- Embedded metadata tags are present (mutagen helps)
- Filenames follow `Artist - Title` pattern
- The song exists on [LRCLIB](https://lrclib.net) or fallback providers
- Your network connection is working
- Try `--search-threads 8` for faster scanning
- Use `--dry-run` to preview matches before downloading

## Visualizer shows nothing

**Check:**
- The selected lyrics directory contains `.wlrc` files
- The current player exposes MPRIS metadata (Linux only)
- The filename stem matches the audio track
- You passed `--wlrc` when using word-level output
- Try `lrc-vis --lrc-dir ./out --wlrc --lrc-file song.wlrc` to bypass playerctl

## Visualizer exits immediately

If using playerctl auto-match, the visualizer exits when no player is detected.
Use `--lrc-file` to pin a specific file:

```bash
lrc-vis --lrc-dir ./out --wlrc --lrc-file ./out/song.wlrc
```

## Command not found after install

**Fix:** Add `~/.local/bin` to your shell `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add this line to your `~/.bashrc`, `~/.zshrc`, or equivalent.

## Permission denied (Linux)

If you see `externally-managed-environment` error:

```bash
pip install --user --break-system-packages lrc-tools
```

Or use a virtual environment:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install lrc-tools
```

## Windows-specific

- `playerctl` is not available on Windows. Use `lrc-vis` with `--lrc-file` and `--play` instead.
- `ffprobe` requires manual PATH configuration or install via Chocolatey: `choco install ffmpeg`
- If the terminal shows garbled characters, ensure your terminal font supports Unicode and enable ANSI escape sequences (Windows Terminal recommended).

## macOS-specific

- `playerctl` may not work with Apple Music. Use `lrc-vis` with `--lrc-file` and `--play` + mpv.
- Install via Homebrew: `brew install playerctl ffmpeg`

## Still stuck?

Open an issue at [github.com/RicknotDev/lrc-tools](https://github.com/RicknotDev/lrc-tools/issues/new/choose).
