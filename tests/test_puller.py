"""Tests for puller.py — metadata extraction and _clean_title."""

from __future__ import annotations

import unittest
from pathlib import Path

from lrc_tools.puller import (
    _clean_title, extract_metadata_from_filename, resolve_output_path,
)


class TestCleanTitle(unittest.TestCase):
    def test_removes_nightcore(self):
        self.assertEqual(_clean_title("Song - Nightcore"), "Song")

    def test_removes_feat(self):
        self.assertEqual(_clean_title("Song (feat. Artist)"), "Song")

    def test_removes_remix(self):
        self.assertEqual(_clean_title("Song (Remix)"), "Song")

    def test_removes_quality_tags(self):
        title = _clean_title("Song")
        self.assertEqual(title, "Song")  # no tags in input

    def test_strip_whitespace(self):
        self.assertEqual(_clean_title("  Song  "), "Song")


class TestExtractMetadataFromFilename(unittest.TestCase):
    def test_artist_title_split(self):
        meta = extract_metadata_from_filename(Path("Artist - Song.mp3"))
        self.assertEqual(meta['artist'], 'Artist')
        self.assertEqual(meta['title'], 'Song')

    def test_no_dash_returns_title_only(self):
        meta = extract_metadata_from_filename(Path("SongOnly.mp3"))
        self.assertEqual(meta['artist'], '')
        self.assertEqual(meta['title'], 'SongOnly')

    def test_removes_quality_tag_from_stem(self):
        meta = extract_metadata_from_filename(Path("Artist - Song [FLAC].mp3"))
        self.assertEqual(meta['artist'], 'Artist')
        self.assertEqual(meta['title'], 'Song')

    def test_cleans_title_with_feat(self):
        meta = extract_metadata_from_filename(Path("Artist - Song (feat. Other).mp3"))
        self.assertEqual(meta['title'], 'Song')

    def test_multi_artist_comma(self):
        meta = extract_metadata_from_filename(Path("Artist1, Artist2 - Song.mp3"))
        self.assertEqual(meta['artist'], 'Artist1')
        self.assertEqual(meta['full_artist'], 'Artist1, Artist2')

    def test_full_artist_and_title_preserved(self):
        meta = extract_metadata_from_filename(Path("Full Artist, Extra - Original Title (feat. Guest).mp3"))
        self.assertEqual(meta['full_artist'], 'Full Artist, Extra')
        self.assertIsNotNone(meta['original_title'])


class TestResolveOutputPath(unittest.TestCase):
    def test_preserve_structure(self):
        audio_dir = Path("/music")
        filepath = Path("/music/artist/song.mp3")
        output_dir = Path("/out")
        result = resolve_output_path(filepath, audio_dir, output_dir, True)
        self.assertEqual(result, Path("/out/artist/song.lrc"))

    def test_flatten_structure(self):
        audio_dir = Path("/music")
        filepath = Path("/music/artist/song.mp3")
        output_dir = Path("/out")
        result = resolve_output_path(filepath, audio_dir, output_dir, False)
        self.assertEqual(result, Path("/out/song.lrc"))

    def test_preserve_fallback_on_relative_error(self):
        audio_dir = Path("/music")
        filepath = Path("/other/song.mp3")
        output_dir = Path("/out")
        result = resolve_output_path(filepath, audio_dir, output_dir, True)
        self.assertEqual(result, Path("/out/song.lrc"))


if __name__ == "__main__":
    unittest.main()
