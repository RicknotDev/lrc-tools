"""Edge cases for LRC parsing, exporting and importing (regressions fixed in 0.5.0)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from lrc_tools import __version__
from lrc_tools.exporters import _secs_to_srt, export_srt
from lrc_tools.importers import import_json, import_srt
from lrc_tools.parser import (
    format_timestamp,
    offset_timestamps,
    parse_lrc,
    parse_lrc_simple,
    parse_metadata,
    repair_lrc,
    split_lrc,
    validate_lrc,
)


class _TmpDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, content, encoding="utf-8", newline=None):
        path = self.dir / name
        with open(path, "w", encoding=encoding, newline=newline) as f:
            f.write(content)
        return path


class TestBom(_TmpDirCase):
    def test_bom_does_not_drop_first_line(self):
        path = self.write("bom.lrc", "[00:01.00]First\n[00:02.00]Second\n", encoding="utf-8-sig")
        self.assertEqual([entry["text"] for entry in parse_lrc(path)], ["First", "Second"])

    def test_bom_metadata(self):
        path = self.write("bom.lrc", "[ti:Song]\n[00:01.00]x\n", encoding="utf-8-sig")
        self.assertEqual(parse_metadata(path)["ti"], "Song")


class TestMultipleTimestamps(_TmpDirCase):
    def test_line_with_two_timestamps_expands(self):
        path = self.write("multi.lrc", "[00:10.00][00:50.00]Chorus\n[00:20.00]Verse\n")
        lines = parse_lrc(path)
        self.assertEqual(
            [(entry["timestamp"], entry["text"]) for entry in lines],
            [(10.0, "Chorus"), (20.0, "Verse"), (50.0, "Chorus")],
        )

    def test_simple_parser_expands_too(self):
        path = self.write("multi.lrc", "[00:10.00][00:50.00]Chorus\n")
        self.assertEqual(parse_lrc_simple(path), [(10.0, "Chorus"), (50.0, "Chorus")])

    def test_validate_accepts_multi_timestamp(self):
        path = self.write("multi.lrc", "[00:10.00][00:50.00]Chorus\n")
        self.assertEqual(validate_lrc(path), [])

    def test_repair_expands(self):
        path = self.write("multi.lrc", "[00:50.00][00:10.00]Chorus\n")
        repair_lrc(path)
        self.assertEqual(path.read_text(encoding="utf-8"), "[00:10.00]Chorus\n[00:50.00]Chorus\n")

    def test_timestamp_without_fraction(self):
        path = self.write("nofrac.lrc", "[01:05]Hello\n")
        self.assertEqual(parse_lrc_simple(path), [(65.0, "Hello")])


class TestStandardTags(_TmpDirCase):
    def test_offset_and_author_tags_are_valid(self):
        path = self.write("tags.lrc", "[offset:+500]\n[au:Someone]\n[tool:x]\n[00:01.00]a\n")
        self.assertEqual(validate_lrc(path), [])
        self.assertEqual(parse_metadata(path)["offset"], "+500")


class TestRounding(unittest.TestCase):
    def test_format_timestamp_never_shows_60_seconds(self):
        self.assertEqual(format_timestamp(59.999), "[01:00.00]")
        self.assertEqual(format_timestamp(119.996), "[02:00.00]")

    def test_format_timestamp_negative_clamps(self):
        self.assertEqual(format_timestamp(-3), "[00:00.00]")

    def test_srt_time_never_shows_60_seconds(self):
        self.assertEqual(_secs_to_srt(59.9996), ("00", "01", "00,000"))
        self.assertEqual(_secs_to_srt(3661.5), ("01", "01", "01,500"))


class TestOffset(_TmpDirCase):
    def test_offset_shifts_all_tags_and_keeps_metadata(self):
        path = self.write("o.lrc", "[ti:T]\n[00:59.50][01:10.00]a\n")
        offset_timestamps(path, 0.5)
        self.assertEqual(path.read_text(encoding="utf-8"), "[ti:T]\n[01:00.00][01:10.50]a\n")


class TestSplit(_TmpDirCase):
    def _lrc(self, n):
        body = "".join(f"[00:{i:02d}.00]l{i}\n" for i in range(n))
        return self.write("s.lrc", body)

    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            split_lrc(self._lrc(3), 0, self.dir)

    def test_even_distribution(self):
        parts = split_lrc(self._lrc(10), 4, self.dir)
        self.assertEqual([len(parse_lrc(p)) for p in parts], [3, 3, 2, 2])

    def test_more_parts_than_lines(self):
        parts = split_lrc(self._lrc(2), 5, self.dir)
        self.assertEqual(len(parts), 2)


class TestImporters(_TmpDirCase):
    def test_srt_with_crlf_multiline(self):
        srt = "1\r\n00:00:01,000 --> 00:00:02,000\r\nline one\r\nline two\r\n\r\n" \
              "2\r\n00:00:03,000 --> 00:00:04,000\r\nnext\r\n"
        path = self.write("c.srt", srt, newline="")
        self.assertEqual(
            import_srt(path),
            [{"timestamp": 1.0, "text": "line one line two"}, {"timestamp": 3.0, "text": "next"}],
        )

    def test_srt_roundtrip_with_bom(self):
        lrc = self.write("r.lrc", "[00:01.50]a\n[00:03.25]b\n", encoding="utf-8-sig")
        srt = export_srt(lrc, self.dir / "r.srt")
        self.assertEqual([e["timestamp"] for e in import_srt(srt)], [1.5, 3.25])

    def test_json_skips_malformed_entries(self):
        data = {"lyrics": [{"timestamp": "2.5", "text": "ok"}, {"text": "no ts"}, "junk", {"timestamp": 1, "text": ""}]}
        path = self.write("j.json", json.dumps(data))
        self.assertEqual(import_json(path), [{"timestamp": 2.5, "text": "ok"}])

    def test_json_top_level_list(self):
        path = self.write("j.json", json.dumps([{"timestamp": 1, "text": "a"}]))
        self.assertEqual(import_json(path), [{"timestamp": 1.0, "text": "a"}])


class TestCliVersion(unittest.TestCase):
    def _run(self, module):
        return subprocess.run(
            [sys.executable, "-m", module, "--version"],
            capture_output=True, text=True, check=False, timeout=60,
        )

    def test_version_flag(self):
        for module in ("lrc_tools.cli.fetch", "lrc_tools.cli.process", "lrc_tools.cli.vis", "lrc_tools.cli.tui"):
            with self.subTest(module=module):
                result = self._run(module)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(__version__, result.stdout)

    def test_help_has_no_raw_markup(self):
        result = subprocess.run(
            [sys.executable, "-m", "lrc_tools.cli.process", "--help"],
            capture_output=True, text=True, check=False, timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("[bold]", result.stdout)
        self.assertNotIn("[dim]", result.stdout)


if __name__ == "__main__":
    unittest.main()
