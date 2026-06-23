"""Tests for CLI argument parsing."""

from __future__ import annotations

import unittest
from unittest import mock

from lrc_tools.cli.fetch import main as fetch_main
from lrc_tools.cli.process import main as process_main
from lrc_tools.cli.vis import main as vis_main


class TestFetchCli(unittest.TestCase):
    @mock.patch('sys.argv', ['lrc-fetch', '--audio-dir', '/tmp', '--output-dir', '/tmp/out',
                              '--search-threads', '1', '--download-threads', '1', '-y'])
    @mock.patch('lrc_tools.cli.fetch.get_audio_files', return_value=[])
    def test_basic_args(self, _mock_files):
        self.assertEqual(fetch_main(), 0)

    @mock.patch('sys.argv', ['lrc-fetch', '--audio-dir', '/nonexistent',
                              '--output-dir', '/tmp/out',
                              '--search-threads', '1', '--download-threads', '1'])
    def test_nonexistent_audio_dir(self):
        self.assertEqual(fetch_main(), 1)

    @mock.patch('sys.argv', ['lrc-fetch', '--help'])
    def test_help_does_not_crash(self):
        with self.assertRaises(SystemExit) as cm:
            fetch_main()
        self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.argv', ['lrc-fetch', '--audio-dir', '/tmp', '--output-dir', '/tmp',
                              '--search-threads', '1', '--download-threads', '1',
                              '--dry-run', '-y'])
    @mock.patch('lrc_tools.cli.fetch.get_audio_files', return_value=[])
    def test_dry_run_flag(self, _mock_files):
        self.assertEqual(fetch_main(), 0)


class TestProcessCli(unittest.TestCase):
    @mock.patch('sys.argv', ['lrc-processor', '--lrc-dir', '/nonexistent',
                              '--output-dir', '/tmp/out'])
    def test_nonexistent_lrc_dir(self):
        self.assertEqual(process_main(), 1)

    @mock.patch('sys.argv', ['lrc-processor', '--help'])
    def test_help_does_not_crash(self):
        with self.assertRaises(SystemExit) as cm:
            process_main()
        self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.argv', ['lrc-processor', '--lrc-dir', '/tmp', '--output-dir', '/tmp',
                              '--wlrc', '--overwrite', '--no-require-audio'])
    @mock.patch('lrc_tools.cli.process.Path.rglob', return_value=[])
    def test_wlrc_flag(self, _mock_rglob):
        self.assertEqual(process_main(), 0)


class TestVisCli(unittest.TestCase):
    @mock.patch('sys.argv', ['lrc-vis', '--lrc-dir', '/nonexistent'])
    def test_nonexistent_lrc_dir(self):
        self.assertEqual(vis_main(), 1)

    @mock.patch('sys.argv', ['lrc-vis', '--help'])
    def test_help_does_not_crash(self):
        with self.assertRaises(SystemExit) as cm:
            vis_main()
        self.assertEqual(cm.exception.code, 0)

    @mock.patch('sys.argv', ['lrc-vis', '--lrc-dir', '/tmp', '--lrc-file', '/nonexistent'])
    def test_nonexistent_lrc_file(self):
        self.assertEqual(vis_main(), 1)


if __name__ == "__main__":
    unittest.main()
