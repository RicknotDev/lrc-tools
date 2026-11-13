"""LRC file parsing and validation utilities."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

# A single "[mm:ss]" or "[mm:ss.xx]" tag. Minutes may exceed two digits.
_TAG_RE = re.compile(r'\[(\d{1,3}):(\d{2}(?:\.\d{1,3})?)\]')
# One or more leading timestamp tags followed by the lyric text,
# e.g. "[00:12.00][00:45.30]Chorus line".
_TIMESTAMP_RE = re.compile(r'((?:\[\d{1,3}:\d{2}(?:\.\d{1,3})?\])+)(.*)')
_METADATA_RE = re.compile(
    r'\[(ti|ar|al|au|by|re|ve|tool|length|offset|#):(.*)\]\s*$', re.IGNORECASE
)

# utf-8-sig transparently strips a BOM (common in files saved by Windows editors).
_ENCODING = 'utf-8-sig'


def _tag_seconds(minutes: str, seconds: str) -> float:
    return int(minutes) * 60 + float(seconds)


def _iter_timed(line: str) -> Iterator[tuple[float, str]]:
    """Yield ``(timestamp, text)`` for every timestamp tag at the start of *line*."""
    match = _TIMESTAMP_RE.match(line)
    if not match:
        return
    tags, text = match.groups()
    text = text.strip()
    for m in _TAG_RE.finditer(tags):
        yield _tag_seconds(*m.groups()), text


def _read_lines(lrc_path: Path, errors: str = 'strict') -> list[str]:
    with open(lrc_path, encoding=_ENCODING, errors=errors) as f:
        return f.read().splitlines()


def parse_lrc(lrc_path: Path) -> list[dict]:
    lines = []
    for raw in _read_lines(lrc_path):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        for timestamp, text in _iter_timed(line):
            if text:
                lines.append({'timestamp': timestamp, 'text': text})
    return sorted(lines, key=lambda x: x['timestamp'])


def parse_lrc_simple(lrc_path: Path) -> list[tuple[float, str]]:
    return [(entry['timestamp'], entry['text']) for entry in parse_lrc(lrc_path)]


def parse_metadata(lrc_path: Path) -> dict[str, str]:
    meta = {}
    for raw in _read_lines(lrc_path, errors='replace'):
        match = _METADATA_RE.match(raw.strip())
        if match:
            key, value = match.groups()
            meta[key.lower()] = value.strip()
    return meta


def _split_seconds(seconds: float) -> tuple[int, float]:
    """Split into (minutes, seconds) rounded to centiseconds without producing ``60.00``."""
    centis = round(max(0.0, seconds) * 100)
    minutes, rest = divmod(centis, 6000)
    return int(minutes), rest / 100


def format_timestamp(seconds: float) -> str:
    minutes, secs = _split_seconds(seconds)
    return f"[{minutes:02d}:{secs:05.2f}]"


def write_lrc(
    output_path: Path,
    lines: list[dict],
    metadata: dict | None = None,
    header_comments: list[str] | None = None,
) -> None:
    with open(output_path, 'w', encoding='utf-8') as f:
        if header_comments:
            for comment in header_comments:
                if not comment.startswith('#'):
                    comment = '# ' + comment
                f.write(f"{comment}\n")
        if metadata:
            for tag, value in [('ti', 'title'), ('ar', 'artist'), ('al', 'album'), ('by', 'by')]:
                if value in metadata:
                    f.write(f"[{tag}:{metadata[value]}]\n")
            f.write("\n")
        for line in sorted(lines, key=lambda x: x['timestamp']):
            f.write(f"{format_timestamp(line['timestamp'])}{line['text']}\n")


def validate_lrc(lrc_path: Path) -> list[str]:
    errors = []
    try:
        lines = _read_lines(lrc_path, errors='replace')
    except OSError as e:
        return [f"Cannot read file: {e}"]

    if not lines:
        return ["Empty file"]

    timestamp_lines = 0
    seen_timestamps: set[float] = set()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if _METADATA_RE.match(stripped):
            continue
        timed = list(_iter_timed(stripped))
        if not timed:
            errors.append(f"L{i}: Unrecognized line format: {stripped[:60]}")
            continue
        for ts, _ in timed:
            ts = round(ts, 3)
            if ts in seen_timestamps:
                errors.append(f"L{i}: Duplicate timestamp [{ts}s]")
            seen_timestamps.add(ts)
        timestamp_lines += 1

    if timestamp_lines == 0:
        errors.append("No timestamped lyric lines found")

    return errors


def repair_lrc(lrc_path: Path, output_path: Path | None = None) -> int:
    """Remove duplicate timestamps, sort lines, write clean LRC. Returns count of issues fixed.

    Lines carrying several timestamps (``[00:10.00][00:50.00]text``) are expanded
    into one line per timestamp.
    """
    timed_lines: list[tuple[float, str]] = []
    metadata_lines = []
    comment_lines = []
    seen_timestamps: set[float] = set()
    duplicates = 0

    for raw in _read_lines(lrc_path, errors='replace'):
        stripped = raw.strip()
        if stripped.startswith('#'):
            comment_lines.append(stripped)
            continue
        if _METADATA_RE.match(stripped):
            metadata_lines.append(stripped)
            continue
        timed = list(_iter_timed(stripped))
        if timed:
            for ts, text in timed:
                key = round(ts, 3)
                if key in seen_timestamps:
                    duplicates += 1
                    continue
                seen_timestamps.add(key)
                timed_lines.append((ts, f"{format_timestamp(ts)}{text}"))
        elif stripped:
            comment_lines.append(f"# {stripped}")

    timed_lines.sort(key=lambda x: x[0])
    out = lrc_path if output_path is None else output_path
    with open(out, 'w', encoding='utf-8') as f:
        for c in comment_lines:
            f.write(c + '\n')
        for m in metadata_lines:
            f.write(m + '\n')
        if metadata_lines:
            f.write('\n')
        for _, line in timed_lines:
            f.write(line + '\n')
    return duplicates


def offset_timestamps(lrc_path: Path, delta: float, output_path: Path | None = None) -> Path:
    out = lrc_path if output_path is None else output_path
    original = '\n'.join(_read_lines(lrc_path, errors='replace')) + '\n'

    def _shift(m: re.Match) -> str:
        new_ts = _tag_seconds(*m.groups()) + delta
        return format_timestamp(new_ts)

    def _shift_line(line: str) -> str:
        match = _TIMESTAMP_RE.match(line)
        if not match:
            return line
        tags, text = match.groups()
        return _TAG_RE.sub(_shift, tags) + text

    shifted = '\n'.join(_shift_line(line) for line in original.split('\n'))
    out.write_text(shifted, encoding='utf-8')
    return out


def merge_lrc(lrc_paths: list[Path], output_path: Path) -> int:
    all_lines = []
    for path in lrc_paths:
        all_lines.extend(parse_lrc(path))
    all_lines.sort(key=lambda x: x['timestamp'])
    write_lrc(output_path, all_lines)
    return len(all_lines)


def split_lrc(lrc_path: Path, n: int, output_dir: Path) -> list[Path]:
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    lines = parse_lrc(lrc_path)
    if not lines:
        return []
    n = min(n, len(lines))
    # Distribute the remainder so chunks differ in size by at most one line.
    base, extra = divmod(len(lines), n)
    created = []
    start = 0
    for i in range(n):
        end = start + base + (1 if i < extra else 0)
        out = output_dir / f"{lrc_path.stem}_part{i + 1}.lrc"
        write_lrc(out, lines[start:end])
        created.append(out)
        start = end
    return created
