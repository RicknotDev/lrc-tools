"""Tests for CLI argument parsing."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from lrc_tools.cli.fetch import main as fetch_main
from lrc_tools.cli.process import main as process_main
from lrc_tools.cli.vis import main as vis_main

TMP = tempfile.gettempdir()
TMPOUT = os.path.join(TMP, "out")
NONEXIST = os.path.join(TMP, "nonexistent_test_dir")


class TestFetchCli(unittest.TestCase):
    @mock.patch('sys.argv', ['lrc-fetch', '--audio-dir', TMP, '--output-dir', TMPOUT,
                              '--search-threads', '1', '--download-threads', '1', '-y'])
    @mock.patch('lrc_tools.cli.fetch.get_audio_files', return_value=[])
    def test_basic_args(self, _mock_files):
        self.assertEqual(fetch_main(), 0)

    @mock.patch('sys.argv', ['lrc-fetch', '--audio-dir', NONEXIST,
                              '--output-dir', TMPOUT,
                              '--search-threads', '1', '--download-threads', '1'])
    def test_nonexistent_audio_dir(self):
        self.assertEqual(fetch_main(), 1)

    @mock.patch('sys.argv', ['lrc-fetch', '--help'])
    def test_help_does_not_crash(self):
        with self.assertRaises(SystemExit) as cm:
            fetch_main()
        self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.argv', ['lrc-fetch', '--audio-dir', TMP, '--output-dir', TMP,
                              '--search-threads', '1', '--download-threads', '1',
                              '--dry-run', '-y'])
    @mock.patch('lrc_tools.cli.fetch.get_audio_files', return_value=[])
    def test_dry_run_flag(self, _mock_files):
        self.assertEqual(fetch_main(), 0)


class TestProcessCli(unittest.TestCase):
    @mock.patch('sys.argv', ['lrc-processor', '--lrc-dir', NONEXIST,
                              '--output-dir', TMPOUT])
    def test_nonexistent_lrc_dir(self):
        self.assertEqual(process_main(), 1)

    @mock.patch('sys.argv', ['lrc-processor', '--help'])
    def test_help_does_not_crash(self):
        with self.assertRaises(SystemExit) as cm:
            process_main()
        self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.argv', ['lrc-processor', '--lrc-dir', TMP, '--output-dir', TMP,
                              '--wlrc', '--overwrite', '--no-require-audio'])
    @mock.patch('lrc_tools.cli.process.Path.rglob', return_value=[])
    def test_wlrc_flag(self, _mock_rglob):
        self.assertEqual(process_main(), 0)


class TestVisCli(unittest.TestCase):
    @mock.patch('sys.argv', ['lrc-vis', '--lrc-dir', NONEXIST])
    def test_nonexistent_lrc_dir(self):
        self.assertEqual(vis_main(), 1)

    @mock.patch('sys.argv', ['lrc-vis', '--help'])
    def test_help_does_not_crash(self):
        with self.assertRaises(SystemExit) as cm:
            vis_main()
        self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.argv', ['lrc-vis', '--lrc-dir', TMP, '--lrc-file', NONEXIST])
    def test_nonexistent_lrc_file(self):
        self.assertEqual(vis_main(), 1)


if __name__ == "__main__":
    unittest.main()
