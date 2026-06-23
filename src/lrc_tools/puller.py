"""Lyrics fetching utilities for lrc-tools."""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib import parse, request
from urllib.error import HTTPError, URLError

from lrc_tools import check_optional

logging.getLogger("syncedlyrics").setLevel(logging.CRITICAL)

FLAC = MP3 = MP4 = OggOpus = OggVorbis = None
try:
    from mutagen.flac import FLAC
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4
    from mutagen.oggopus import OggOpus
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

_syncedlyrics_module = check_optional(
    "syncedlyrics",
    'python3 -m pip install --user "lrc-tools[full]"',
    "fallback synced lyrics search",
)
if _syncedlyrics_module is not None:
    syncedlyrics_search = _syncedlyrics_module.search
    SYNCEDLYRICS_AVAILABLE = True
else:
    syncedlyrics_search = None
    SYNCEDLYRICS_AVAILABLE = False

_VERSION_PATTERNS = [
    " - Nightcore", " - Slowed", " - slowed", " - Sped Up", " - SPED UP",
    " - Slowed Down", " - Slowed & Reverb", " - Slowed & Reverbed",
    " - sped up", " - speed up", " - spedup", " - super slowed",
    " - super spedup", " - ultra slowed", " - Instrumental", " - Radio Edit",
    " - Extended", " - extended", " - Single Version", " - Album Version",
    " - Remaster", " - Remastered", " - Official Audio", " - Official Video",
    " - Lyrics", " - lyric video", " - Audio", " - Video", " - Visualizer",
    " - Music Video", " - NIGHTCORE", " - Hardstyle Slowed", " - original",
    " - old mix", " - v2", " - v3", " - Mega Mix", " - Mega Mix Slowed",
    " - VIRAL SLOWED", " - 2009 N3WGR0UNDZ V3RS10N!",
]
_FEAT_MARKERS = [" (feat.", " (ft.", " (From ", " (w ", " (with ", " (feat ", " (ft "]
_BONUS_MARKERS = [" (Bonus)", " (Bonus Track)", " (BONUS TRACK)"]
_TRAILING_ARTIFACTS = [" 3", " -3", " _.", " -.", " -)", " -c", " 33"]
_QUALITY_TAGS = ["[FLAC]", "[MP3]", "[320]", "[256]", "[128]"]


def get_audio_metadata(filepath: Path) -> Optional[Dict[str, str]]:
    if not MUTAGEN_AVAILABLE:
        return None
    try:
        ext = filepath.suffix.lower()

        if ext == ".flac" and FLAC is not None:
            audio = FLAC(filepath)
        elif ext == ".mp3" and MP3 is not None:
            audio = MP3(filepath)
        elif ext in (".m4a", ".mp4") and MP4 is not None:
            audio = MP4(filepath)
        elif ext in (".ogg", ".oga") and OggVorbis is not None:
            audio = OggVorbis(filepath)
        elif ext == ".opus" and OggOpus is not None:
            audio = OggOpus(filepath)
        else:
            return None

        if ext in (".m4a", ".mp4"):
            artist_values = audio.get("\xa9ART", [None]) or [None]
            title_values = audio.get("\xa9nam", [None]) or [None]
            artist = artist_values[0]
            title = title_values[0]
        else:
            artist_tag = audio.get("artist") or audio.get("ARTIST")
            title_tag = audio.get("title") or audio.get("TITLE")
            artist = (
                (artist_tag[0] if isinstance(artist_tag, list) else artist_tag)
                if artist_tag else None
            )
            title = (
                (title_tag[0] if isinstance(title_tag, list) else title_tag)
                if title_tag else None
            )

        if artist and title:
            return {"artist": str(artist), "title": str(title)}
    except Exception:
        pass
    return None


def _clean_title(raw_title: str) -> str:
    title = raw_title
    for pattern in _VERSION_PATTERNS:
        if pattern in title:
            title = title.split(pattern)[0]
    for marker in _FEAT_MARKERS:
        if marker in title:
            title = title.split(marker)[0]
    if title.endswith(" (Remix)"):
        title = title[:-8]
    elif " - Remix" in title:
        title = title.split(" - Remix")[0]
    for marker in _BONUS_MARKERS:
        if marker in title:
            title = title.split(marker)[0]
    title = title.strip()
    for suffix in _TRAILING_ARTIFACTS:
        if title.endswith(suffix):
            title = title[:-len(suffix)].strip()
    if " #" in title:
        title = title.split(" #")[0].strip()
    title = title.replace("\u271e", "").replace("\u266b\U0001f146", "").strip()
    return title


def extract_metadata_from_filename(filepath: Path) -> Dict[str, Optional[str]]:
    stem = filepath.stem
    for tag in _QUALITY_TAGS:
        stem = stem.replace(tag, "")
    stem = stem.strip()

    if " - " not in stem:
        return {
            "artist": "",
            "title": stem,
            "full_artist": None,
            "original_title": None,
        }

    full_artist, full_title = stem.split(" - ", 1)
    full_artist = full_artist.strip()
    full_title = full_title.strip()

    artist = full_artist.split(", ")[0].strip() if ", " in full_artist else full_artist
    title = _clean_title(full_title)

    return {
        "artist": artist,
        "title": title,
        "full_artist": full_artist if full_artist != artist else None,
        "original_title": full_title if full_title != title else None,
    }


def extract_metadata(filepath: Path) -> Dict[str, Optional[str]]:
    tag_meta = get_audio_metadata(filepath)
    filename_meta = extract_metadata_from_filename(filepath)

    if tag_meta:
        return {
            "artist": tag_meta["artist"],
            "title": tag_meta["title"],
            "full_artist": filename_meta.get("full_artist"),
            "original_title": filename_meta.get("original_title"),
        }
    return filename_meta


def search_lrclib(
    artist: str,
    title: str,
    duration: Optional[float] = None,
    max_retries: int = 3,
    retry_backoff: float = 0.5,
) -> List[Dict]:
    params: Dict[str, str] = {"artist_name": artist, "track_name": title}
    if duration is not None:
        params["duration"] = str(int(duration))

    url = f"https://lrclib.net/api/search?{parse.urlencode(params)}"

    for attempt in range(max_retries):
        try:
            with request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                return data if isinstance(data, list) else []
        except (HTTPError, URLError, TimeoutError):
            if attempt == max_retries - 1:
                return []
            time.sleep(retry_backoff * (attempt + 1))
    return []


def _pick_lyrics(result: Dict, prefer_synced: bool = True) -> Optional[str]:
    if prefer_synced:
        return result.get("syncedLyrics") or result.get("plainLyrics")
    return result.get("plainLyrics") or result.get("syncedLyrics")


def search_syncedlyrics(artist: str, title: str) -> Optional[str]:
    if not SYNCEDLYRICS_AVAILABLE or syncedlyrics_search is None:
        return None
    try:
        result = syncedlyrics_search(
            f"{artist} {title}", providers=["lrclib", "netease"]
        )
        return result or None
    except Exception:
        return None


def search_song(
    song_info: Tuple[Path, Dict],
    prefer_synced: bool = True,
    request_delay: float = 0.05,
    max_retries: int = 3,
    retry_backoff: float = 0.5,
) -> Dict:
    filepath, metadata = song_info
    time.sleep(request_delay)

    def _lrclib_hit(artist, title) -> Optional[str]:
        results = search_lrclib(artist, title, max_retries=max_retries, retry_backoff=retry_backoff)
        if results:
            return _pick_lyrics(results[0], prefer_synced)
        return None

    try:
        artist = metadata["artist"]
        title = metadata["title"]

        content = _lrclib_hit(artist, title)
        if content:
            return {"status": "found", "song": song_info, "source": "lrclib", "content": content}

        original_title = metadata.get("original_title")
        if original_title and original_title != title:
            content = _lrclib_hit(artist, original_title)
            if content:
                return {"status": "found", "song": song_info, "source": "lrclib", "content": content}

        full_artist = metadata.get("full_artist")
        if full_artist and full_artist != artist:
            content = _lrclib_hit(full_artist, title)
            if content:
                return {"status": "found", "song": song_info, "source": "lrclib", "content": content}

        content = search_syncedlyrics(artist, title)
        if content:
            return {"status": "found", "song": song_info, "source": "syncedlyrics", "content": content}

        return {"status": "not_found", "song": song_info}
    except Exception:
        return {"status": "error", "song": song_info}


def resolve_output_path(
    filepath: Path,
    audio_dir: Path,
    output_dir: Path,
    preserve_structure: bool = True,
) -> Path:
    if preserve_structure:
        try:
            rel = filepath.relative_to(audio_dir)
            out = output_dir / rel.with_suffix(".lrc")
        except ValueError:
            out = output_dir / filepath.with_suffix(".lrc").name
    else:
        out = output_dir / filepath.with_suffix(".lrc").name
    return out


def save_lyrics(content: str, output_path: Path) -> bool:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            existing = output_path.read_text(encoding="utf-8")
            if existing == content:
                return True  # ponytail: skip backup if content is identical
            from lrc_tools.core import backup_file
            backup_file(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except IOError:
        return False
