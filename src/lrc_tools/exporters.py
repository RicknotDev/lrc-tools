"""Export LRC lyrics to SRT (subtitles) and JSON."""

import json
from pathlib import Path

from lrc_tools.parser import parse_lrc, parse_metadata


def _lrc_to_srt_entries(lines: list[dict]) -> list[str]:
    """Return list of SRT blocks (index + timing + text)."""
    blocks = []
    for i, line in enumerate(lines, 1):
        ts = line['timestamp']
        next_ts = lines[i]['timestamp'] if i < len(lines) else ts + 4.0
        start_h, start_m, start_s = _secs_to_srt(ts)
        end_h, end_m, end_s = _secs_to_srt(next_ts)
        text = line['text'].replace('\n', ' ')
        blocks.append(f"{i}\n{start_h}:{start_m}:{start_s} --> {end_h}:{end_m}:{end_s}\n{text}\n")
    return blocks


def _secs_to_srt(secs: float) -> tuple:
    # Work in integer milliseconds so 59.9996s becomes 00:01:00,000, never 00:00:60,000.
    total_ms = round(max(0.0, secs) * 1000)
    h, rem = divmod(total_ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}", f"{m:02d}", f"{s:02d},{ms:03d}"


def export_srt(lrc_path: Path, output_path: Path) -> Path:
    lines = parse_lrc(lrc_path)
    blocks = _lrc_to_srt_entries(lines)
    output_path.write_text('\n'.join(blocks), encoding='utf-8')
    return output_path


def export_json(lrc_path: Path, output_path: Path) -> Path:
    lines = parse_lrc(lrc_path)
    meta = parse_metadata(lrc_path)
    data = {
        "metadata": meta,
        "source": str(lrc_path),
        "lyrics": [{k: v for k, v in entry.items()} for entry in lines],
    }
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    return output_path


def export_lrc(lrc_path: Path, output_path: Path, fmt: str) -> Path | None:
    mapping = {"srt": export_srt, "json": export_json}
    fn = mapping.get(fmt.lower())
    if fn is None:
        raise ValueError(f"Unsupported export format: {fmt!r} (supported: srt, json)")
    return fn(lrc_path, output_path)
