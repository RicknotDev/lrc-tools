"""LRC file parsing and validation utilities."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


_TIMESTAMP_RE = re.compile(r'\[(\d{1,2}):(\d{2}(?:\.\d{1,3})?)\](.*)')
_METADATA_RE = re.compile(r'\[(ti|ar|al|by|re|ve|length):(.+)\]', re.IGNORECASE)


def parse_lrc(lrc_path: Path) -> List[Dict]:
    lines = []
    with open(lrc_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = _TIMESTAMP_RE.match(line)
            if match:
                minutes, seconds, text = match.groups()
                timestamp = float(minutes) * 60 + float(seconds)
                text = text.strip()
                if text:
                    lines.append({'timestamp': timestamp, 'text': text})
    return sorted(lines, key=lambda x: x['timestamp'])


def parse_lrc_simple(lrc_path: Path) -> List[Tuple[float, str]]:
    lines = []
    pattern = re.compile(r'\[(\d{1,2}):(\d{2}\.\d{1,3})\](.+)')
    with open(lrc_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = pattern.match(line)
            if match:
                minutes, seconds, text = match.groups()
                timestamp = int(minutes) * 60 + float(seconds)
                text = text.strip()
                if text:
                    lines.append((timestamp, text))
    return sorted(lines, key=lambda x: x[0])


def parse_metadata(lrc_path: Path) -> Dict[str, str]:
    meta = {}
    with open(lrc_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            match = _METADATA_RE.match(line)
            if match:
                key, value = match.groups()
                meta[key.lower()] = value.strip()
    return meta


def format_timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"[{minutes:02d}:{secs:05.2f}]"


def write_lrc(output_path: Path, lines: List[Dict], metadata: Dict = None, header_comments: List[str] = None):
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


def validate_lrc(lrc_path: Path) -> List[str]:
    errors = []
    try:
        text = lrc_path.read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        return [f"Cannot read file: {e}"]

    lines = text.splitlines()
    if not lines:
        return ["Empty file"]

    timestamp_lines = 0
    seen_timestamps = set()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if _METADATA_RE.match(stripped):
            continue
        match = _TIMESTAMP_RE.match(stripped)
        if match:
            minutes, seconds, content = match.groups()
            ts = round(float(minutes) * 60 + float(seconds), 3)
            if ts in seen_timestamps:
                errors.append(f"L{i}: Duplicate timestamp [{ts}s]")
            seen_timestamps.add(ts)
            timestamp_lines += 1
        else:
            errors.append(f"L{i}: Unrecognized line format: {stripped[:60]}")

    if timestamp_lines == 0:
        errors.append("No timestamped lyric lines found")

    return errors


def repair_lrc(lrc_path: Path, output_path: Optional[Path] = None) -> int:
    """Remove duplicate timestamps, sort lines, write clean LRC. Returns count of issues fixed."""
    raw_lines = []
    metadata_lines = []
    comment_lines = []
    seen_timestamps = set()
    duplicates = 0

    with open(lrc_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            stripped = line.rstrip('\n\r')
            if stripped.startswith('#'):
                comment_lines.append(stripped)
                continue
            if _METADATA_RE.match(stripped):
                metadata_lines.append(stripped)
                continue
            match = _TIMESTAMP_RE.match(stripped)
            if match:
                minutes, seconds, content = match.groups()
                ts = round(float(minutes) * 60 + float(seconds), 3)
                if ts in seen_timestamps:
                    duplicates += 1
                    continue
                seen_timestamps.add(ts)
                raw_lines.append((ts, stripped))
            else:
                if stripped:
                    comment_lines.append(f"# {stripped}")

    raw_lines.sort(key=lambda x: x[0])
    out = lrc_path if output_path is None else output_path
    with open(out, 'w', encoding='utf-8') as f:
        for c in comment_lines:
            f.write(c + '\n')
        for m in metadata_lines:
            f.write(m + '\n')
        if metadata_lines:
            f.write('\n')
        for _, line in raw_lines:
            f.write(line + '\n')
    return duplicates


def offset_timestamps(lrc_path: Path, delta: float, output_path: Optional[Path] = None) -> Path:
    out = lrc_path if output_path is None else output_path
    with open(lrc_path, 'r', encoding='utf-8', errors='replace') as f:
        original = f.read()

    def _shift(m):
        minutes, seconds, text = m.groups()
        orig_ts = float(minutes) * 60 + float(seconds)
        new_ts = max(0.0, orig_ts + delta)
        new_m = int(new_ts // 60)
        new_s = new_ts % 60
        return f"[{new_m:02d}:{new_s:05.2f}]{text}"

    shifted = _TIMESTAMP_RE.sub(_shift, original)
    out.write_text(shifted, encoding='utf-8')
    return out


def merge_lrc(lrc_paths: List[Path], output_path: Path) -> int:
    all_lines = []
    for path in lrc_paths:
        all_lines.extend(parse_lrc(path))
    all_lines.sort(key=lambda x: x['timestamp'])
    write_lrc(output_path, all_lines)
    return len(all_lines)


def split_lrc(lrc_path: Path, n: int, output_dir: Path) -> List[Path]:
    lines = parse_lrc(lrc_path)
    if not lines:
        return []
    chunk_size = max(1, len(lines) // n)
    created = []
    for i in range(n):
        start = i * chunk_size
        end = None if i == n - 1 else start + chunk_size
        chunk = lines[start:end]
        if not chunk:
            break
        out = output_dir / f"{lrc_path.stem}_part{i + 1}.lrc"
        write_lrc(out, chunk)
        created.append(out)
    return created
