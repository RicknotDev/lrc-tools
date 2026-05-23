# File Formats

This page explains the lyric formats used by `lrc-tools`.

## `.lrc`

`.lrc` stores timestamps for whole lyric lines or phrases.

### Example

```/dev/null/example.lrc#L1-4
[00:12.00]Hello darkness, my old friend
[00:17.20]I've come to talk with you again
[00:22.10]Because a vision softly creeping
[00:27.40]Left its seeds while I was sleeping
```

## `.wlrc`

`.wlrc` is the project's word-level variant. Each timestamp maps to a single word so the visualizer can advance word by word.

### Example

```/dev/null/example.wlrc#L1-6
[00:12.00]Hello
[00:12.45]darkness,
[00:13.10]my
[00:13.40]old
[00:13.80]friend
[00:17.20]I've
```

## When each format is used

- `lrc-fetch` downloads `.lrc`
- `lrc-processor --wlrc` converts `.lrc` into `.wlrc`
- `lrc-vis --wlrc` renders word-level lyrics

## Matching rules

The lyric filename should match the audio filename stem.

- `Artist - Song.mp3`
- `Artist - Song.lrc`
- `Artist - Song.wlrc`

## Notes

- `.lrc` is better for portability.
- `.wlrc` is better for terminal karaoke-style playback.
- If no audio file is available, generated word timing is estimated.
