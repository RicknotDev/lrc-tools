"""Tests for exporters.py and importers.py — SRT/JSON roundtrip."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lrc_tools.exporters import export_srt, export_json
from lrc_tools.importers import import_srt, import_json
from lrc_tools.parser import write_lrc, parse_lrc


class TestExportImport(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _make_lrc(self, name: str = "test") -> Path:
        lrc = self.tmp / f"{name}.lrc"
        lines = [
            {'timestamp': 1.0, 'text': 'Hello world'},
            {'timestamp': 2.5, 'text': 'Second line'},
            {'timestamp': 4.0, 'text': 'Third'},
        ]
        write_lrc(lrc, lines, metadata={'title': name, 'artist': 'Test'})
        return lrc

    def test_export_srt(self):
        lrc = self._make_lrc()
        srt = self.tmp / "test.srt"
        export_srt(lrc, srt)
        content = srt.read_text(encoding='utf-8')
        self.assertIn('-->', content)
        self.assertIn('Hello world', content)
        self.assertIn('Second line', content)

    def test_export_json(self):
        lrc = self._make_lrc()
        js = self.tmp / "test.json"
        export_json(lrc, js)
        data = json.loads(js.read_text(encoding='utf-8'))
        self.assertIn('metadata', data)
        self.assertIn('lyrics', data)
        self.assertEqual(len(data['lyrics']), 3)
        self.assertEqual(data['metadata'].get('ti'), 'test')

    def test_roundtrip_srt(self):
        lrc = self._make_lrc()
        srt = self.tmp / "round.srt"
        export_srt(lrc, srt)
        imported = import_srt(srt)
        self.assertEqual(len(imported), 3)
        self.assertEqual(imported[0]['text'], 'Hello world')

    def test_roundtrip_json(self):
        lrc = self._make_lrc()
        js = self.tmp / "round.json"
        export_json(lrc, js)
        imported = import_json(js)
        self.assertEqual(len(imported), 3)
        self.assertEqual(imported[0]['text'], 'Hello world')

    def test_import_srt_preserves_timestamps(self):
        lrc = self._make_lrc()
        srt = self.tmp / "ts.srt"
        export_srt(lrc, srt)
        imported = import_srt(srt)
        orig = parse_lrc(lrc)
        for orig_line, imp_line in zip(orig, imported):
            self.assertAlmostEqual(orig_line['timestamp'], imp_line['timestamp'], places=1)

    def test_export_empty_lrc(self):
        lrc = self.tmp / "empty.lrc"
        write_lrc(lrc, [])
        srt = self.tmp / "empty.srt"
        export_srt(lrc, srt)
        self.assertTrue(srt.exists())
        self.assertEqual(srt.read_text(encoding='utf-8'), '')


if __name__ == "__main__":
    unittest.main()
