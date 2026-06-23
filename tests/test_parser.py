"""Tests for parser.py — parse, validate, repair, offset, merge, split."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lrc_tools.parser import (
    parse_lrc, parse_lrc_simple, parse_metadata, format_timestamp,
    write_lrc, validate_lrc, repair_lrc, offset_timestamps, merge_lrc, split_lrc,
)


class TestParseLrc(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _write(self, name: str, content: str) -> Path:
        p = self.tmp / name
        p.write_text(content, encoding='utf-8')
        return p

    def test_parse_basic(self):
        f = self._write("test.lrc", "[00:01.00]Hello\n[00:02.50]World\n")
        lines = parse_lrc(f)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]['text'], 'Hello')
        self.assertEqual(lines[0]['timestamp'], 1.0)
        self.assertEqual(lines[1]['text'], 'World')
        self.assertEqual(lines[1]['timestamp'], 2.5)

    def test_parse_sorts_by_timestamp(self):
        f = self._write("unsorted.lrc", "[00:03.00]Last\n[00:01.00]First\n")
        lines = parse_lrc(f)
        self.assertEqual(lines[0]['text'], 'First')
        self.assertEqual(lines[1]['text'], 'Last')

    def test_parse_skips_comments_and_empty(self):
        f = self._write("comments.lrc", "# comment\n[00:01.00]A\n\n[00:02.00]B\n")
        lines = parse_lrc(f)
        self.assertEqual(len(lines), 2)

    def test_parse_skips_metadata_tags(self):
        f = self._write("meta.lrc", "[ti:Test]\n[ar:Artist]\n[00:01.00]A\n[00:02.00]B\n")
        lines = parse_lrc(f)
        self.assertEqual(len(lines), 2)

    def test_parse_simple(self):
        f = self._write("simple.lrc", "[00:01.00]Hello\n[00:02.50]World\n")
        lines = parse_lrc_simple(f)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], (1.0, 'Hello'))

    def test_parse_metadata(self):
        f = self._write("meta.lrc", "[ti:Test Song]\n[ar:Artist Name]\n[al:Album]\n[00:01.00]A\n")
        meta = parse_metadata(f)
        self.assertEqual(meta.get('ti'), 'Test Song')
        self.assertEqual(meta.get('ar'), 'Artist Name')
        self.assertEqual(meta.get('al'), 'Album')

    def test_format_timestamp(self):
        self.assertEqual(format_timestamp(0), "[00:00.00]")
        self.assertEqual(format_timestamp(1.5), "[00:01.50]")
        self.assertEqual(format_timestamp(65.0), "[01:05.00]")

    def test_write_lrc(self):
        lines = [{'timestamp': 1.0, 'text': 'Hello'}, {'timestamp': 2.5, 'text': 'World'}]
        out = self.tmp / "out.lrc"
        write_lrc(out, lines)
        content = out.read_text(encoding='utf-8')
        self.assertIn('[00:01.00]Hello', content)
        self.assertIn('[00:02.50]World', content)

    def test_write_lrc_with_metadata(self):
        lines = [{'timestamp': 1.0, 'text': 'A'}]
        out = self.tmp / "meta_out.lrc"
        write_lrc(out, lines, metadata={'title': 'Test', 'artist': 'Me'})
        content = out.read_text(encoding='utf-8')
        self.assertIn('[ti:Test]', content)
        self.assertIn('[ar:Me]', content)

    def test_validate_ok(self):
        f = self._write("good.lrc", "[00:01.00]Hello\n[00:02.00]World\n")
        self.assertEqual(validate_lrc(f), [])

    def test_validate_duplicate(self):
        f = self._write("dup.lrc", "[00:01.00]A\n[00:01.00]B\n")
        errs = validate_lrc(f)
        self.assertTrue(any('Duplicate' in e for e in errs))

    def test_validate_bad_line(self):
        f = self._write("bad.lrc", "[00:01.00]A\nbadline\n")
        errs = validate_lrc(f)
        self.assertTrue(any('Unrecognized' in e for e in errs))

    def test_validate_empty(self):
        f = self._write("empty.lrc", "")
        errs = validate_lrc(f)
        self.assertTrue(any('Empty' in e for e in errs))

    def test_validate_no_timestamps(self):
        f = self._write("no_ts.lrc", "just some text\n")
        errs = validate_lrc(f)
        self.assertTrue(any('No timestamped' in e for e in errs))

    def test_repair_removes_duplicates(self):
        f = self._write("dup.lrc", "[00:01.00]A\n[00:01.00]B\n[00:02.00]C\n")
        out = self.tmp / "repaired.lrc"
        fixed = repair_lrc(f, out)
        self.assertEqual(fixed, 1)
        lines = parse_lrc(out)
        self.assertEqual(len(lines), 2)

    def test_offset_timestamps(self):
        f = self._write("offset.lrc", "[00:01.00]A\n[00:02.00]B\n")
        out = self.tmp / "offset_out.lrc"
        offset_timestamps(f, 0.5, out)
        lines = parse_lrc(out)
        self.assertAlmostEqual(lines[0]['timestamp'], 1.5)
        self.assertAlmostEqual(lines[1]['timestamp'], 2.5)

    def test_offset_negative_clamps_to_zero(self):
        f = self._write("neg.lrc", "[00:00.50]A\n[00:02.00]B\n")
        out = self.tmp / "neg_out.lrc"
        offset_timestamps(f, -1.0, out)
        lines = parse_lrc(out)
        self.assertAlmostEqual(lines[0]['timestamp'], 0.0)
        self.assertAlmostEqual(lines[1]['timestamp'], 1.0)

    def test_merge_lrc(self):
        a = self._write("a.lrc", "[00:02.00]B\n[00:01.00]A\n")
        b = self._write("b.lrc", "[00:03.00]C\n")
        out = self.tmp / "merged.lrc"
        count = merge_lrc([a, b], out)
        self.assertEqual(count, 3)
        lines = parse_lrc(out)
        self.assertEqual([entry['text'] for entry in lines], ['A', 'B', 'C'])

    def test_split_lrc(self):
        f = self._write("long.lrc", "[00:01.00]A\n[00:02.00]B\n[00:03.00]C\n[00:04.00]D\n")
        parts = split_lrc(f, 2, self.tmp)
        self.assertEqual(len(parts), 2)
        a = parse_lrc(parts[0])
        b = parse_lrc(parts[1])
        self.assertEqual(len(a), 2)
        self.assertEqual(len(b), 2)
        self.assertEqual(a[0]['text'], 'A')


if __name__ == "__main__":
    unittest.main()
