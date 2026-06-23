"""Import SRT or JSON files into LRC format."""

import json
import re
from pathlib import Path
from typing import Dict, List



_SRT_TIME_RE = re.compile(
    r'(\d{1,2}):(\d{2}):(\d{2}[,.]\d{1,3})'
)


def _srt_time_to_secs(time_str: str) -> float:
    m = _SRT_TIME_RE.match(time_str.strip())
    if not m:
        return 0.0
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s.replace(',', '.'))


def import_srt(srt_path: Path) -> List[Dict]:
    text = srt_path.read_text(encoding='utf-8', errors='replace')
    lines = []
    # Simple SRT parser: extract text between timestamps
    block_re = re.compile(
        r'\d+\s*\n'
        r'(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*'
        r'(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*\n'
        r'(.+?)(?=\n\s*\n|\Z)',
        re.DOTALL
    )
    for m in block_re.finditer(text):
        start = _srt_time_to_secs(m.group(1))
        content = m.group(3).strip().replace('\n', ' ')
        if content:
            lines.append({'timestamp': start, 'text': content})
    return sorted(lines, key=lambda x: x['timestamp'])


def import_json(json_path: Path) -> List[Dict]:
    data = json.loads(json_path.read_text(encoding='utf-8'))
    lyrics = data.get('lyrics', data)
    if isinstance(lyrics, list):
        return sorted(
            (entry for entry in lyrics if entry.get('text')),
            key=lambda x: x['timestamp']
        )
    return []


def import_lrc(src_path: Path, fmt: str) -> List[Dict]:
    mapping = {"srt": import_srt, "json": import_json}
    fn = mapping.get(fmt.lower())
    if fn is None:
        raise ValueError(f"Unsupported import format: {fmt!r} (supported: srt, json)")
    return fn(src_path)
