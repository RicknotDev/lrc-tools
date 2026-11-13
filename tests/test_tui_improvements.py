"""Tests for the TUI improvements in 0.6.0: help screen, lyrics check, task cancel, next-step hints."""

from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

from lrc_tools import core
from lrc_tools.tui.process_runner import CANCELLED, ProcessRunner, format_elapsed
from lrc_tools.tui.screens.lyrics_check import repair_reports, scan_lyrics
from lrc_tools.tui.widgets.status_panel import next_step


class _LibraryCase(unittest.TestCase):
    """A throwaway music dir with raw/processed lyric folders."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.music = root / "music"
        self.raw = root / "raw"
        self.processed = root / "processed"
        for d in (self.music, self.raw, self.processed):
            d.mkdir()
        self.state = core.AppState(music_dir=self.music, lyrics_raw=self.raw, lyrics_processed=self.processed)

    def tearDown(self):
        self._tmp.cleanup()

    def lrc(self, name: str, body: str) -> Path:
        path = self.raw / f"{name}.lrc"
        path.write_text(body, encoding="utf-8")
        return path


class TestNextStep(unittest.TestCase):
    def stats(self, **kw):
        base = {"music_dir": str(Path.home()), "audio": 10, "lrc": 10, "wlrc": 10}
        return {**base, **kw}

    def test_missing_music_dir(self):
        self.assertIn("carpeta de música", next_step(self.stats(music_dir="/no/existe/xyz", lrc=0, wlrc=0)))

    def test_no_songs(self):
        self.assertIn("No hay canciones", next_step(self.stats(audio=0, lrc=0, wlrc=0)))

    def test_processed_lyrics_without_local_audio_are_ready(self):
        self.assertIn("visualizador", next_step(self.stats(audio=0)))

    def test_no_lyrics(self):
        self.assertIn("Descargá las letras", next_step(self.stats(lrc=0, wlrc=0)))

    def test_pending_processing(self):
        self.assertIn("Procesá 4 letras", next_step(self.stats(lrc=10, wlrc=6)))

    def test_all_done(self):
        self.assertIn("visualizador", next_step(self.stats()))


class TestLyricsCheck(_LibraryCase):
    def test_scan_classifies_and_sorts_problems_first(self):
        self.lrc("good", "[00:01.00]a\n[00:02.00]b\n")
        self.lrc("dupes", "[00:01.00]a\n[00:01.00]again\n")
        self.lrc("plain", "just text\nno timestamps\n")
        reports = {r.path.stem: r for r in scan_lyrics(self.raw)}
        self.assertTrue(reports["good"].ok)
        self.assertTrue(reports["dupes"].fixable)
        self.assertFalse(reports["plain"].ok)
        self.assertFalse(reports["plain"].fixable)
        self.assertTrue(scan_lyrics(self.raw)[-1].ok)

    def test_repair_backs_up_and_fixes(self):
        path = self.lrc("dupes", "[00:02.00]b\n[00:01.00]a\n[00:01.00]again\n")
        files, issues = repair_reports(scan_lyrics(self.raw))
        self.assertEqual((files, issues), (1, 1))
        self.assertEqual(path.read_text(encoding="utf-8"), "[00:01.00]a\n[00:02.00]b\n")
        self.assertTrue((self.raw / "dupes.lrc.bak").is_file())
        self.assertTrue(all(r.ok for r in scan_lyrics(self.raw)))

    def test_repair_skips_plain_lyrics(self):
        path = self.lrc("plain", "only text\n")
        self.assertEqual(repair_reports(scan_lyrics(self.raw)), (0, 0))
        self.assertEqual(path.read_text(encoding="utf-8"), "only text\n")


class TestProcessRunner(unittest.IsolatedAsyncioTestCase):
    async def test_streams_output(self):
        lines: list[str] = []
        code = await ProcessRunner().run([sys.executable, "-c", "print('hola'); print('chau')"], lines.append)
        self.assertEqual((code, lines), (0, ["hola", "chau"]))

    async def test_child_cannot_block_on_stdin(self):
        lines: list[str] = []
        code = await asyncio.wait_for(
            ProcessRunner().run([sys.executable, "-c", "import sys; print(repr(sys.stdin.read()))"], lines.append),
            timeout=30,
        )
        self.assertEqual((code, lines), (0, ["''"]))

    async def test_cancel(self):
        runner = ProcessRunner()
        task = asyncio.create_task(runner.run([sys.executable, "-c", "import time; time.sleep(60)"], lambda _: None))
        for _ in range(100):
            if runner.running:
                break
            await asyncio.sleep(0.05)
        self.assertTrue(runner.cancel())
        self.assertEqual(await asyncio.wait_for(task, timeout=30), CANCELLED)
        self.assertFalse(runner.cancel())

    def test_format_elapsed(self):
        self.assertEqual(format_elapsed(75.4), "1:15")


@unittest.skipUnless(core.textual_available(), "textual not installed")
class TestTuiScreens(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        for d in ("music", "raw", "processed"):
            (root / d).mkdir()
        (root / "raw" / "dupes.lrc").write_text("[00:01.00]a\n[00:01.00]b\n", encoding="utf-8")
        self.state = core.AppState(music_dir=root / "music", lyrics_raw=root / "raw", lyrics_processed=root / "processed")

    def tearDown(self):
        self._tmp.cleanup()

    async def test_menu_fits_small_terminal(self):
        from textual.widgets import ListView

        from lrc_tools.tui.app import LrcToolsApp

        app = LrcToolsApp(self.state)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            menu = pilot.app.screen.query_one("#menu", ListView)
            self.assertEqual(len(menu.children), 11)
            # Every item is visible without scrolling.
            self.assertEqual(menu.max_scroll_y, 0)

    async def test_question_mark_opens_and_closes_help(self):
        from lrc_tools.tui.app import LrcToolsApp
        from lrc_tools.tui.widgets.help_screen import HelpScreen

        app = LrcToolsApp(self.state)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("question_mark")
            await pilot.pause()
            self.assertIsInstance(pilot.app.screen, HelpScreen)
            await pilot.press("escape")
            await pilot.pause()
            self.assertNotIsInstance(pilot.app.screen, HelpScreen)

    async def test_c_opens_lyrics_check_with_results(self):
        from textual.widgets import DataTable

        from lrc_tools.tui.app import LrcToolsApp
        from lrc_tools.tui.screens.lyrics_check import LyricsCheckScreen

        app = LrcToolsApp(self.state)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("c")
            for _ in range(40):
                await pilot.pause(0.05)
                screen = pilot.app.screen
                if isinstance(screen, LyricsCheckScreen) and screen.reports:
                    break
            self.assertIsInstance(pilot.app.screen, LyricsCheckScreen)
            self.assertEqual(pilot.app.screen.query_one("#check-table", DataTable).row_count, 1)
            self.assertTrue(pilot.app.screen.reports[0].fixable)

    async def test_confirm_dialog_escape_means_no(self):
        from lrc_tools.tui.app import LrcToolsApp
        from lrc_tools.tui.widgets.confirm_dialog import ConfirmDialog

        results: list[bool] = []
        app = LrcToolsApp(self.state)
        async with app.run_test() as pilot:
            pilot.app.push_screen(ConfirmDialog("¿Seguro?"), results.append)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
        self.assertEqual(results, [False])

    async def test_task_screen_reports_missing_music_dir(self):
        from textual.widgets import Static

        from lrc_tools.tui.app import LrcToolsApp
        from lrc_tools.tui.screens.task import TaskScreen

        self.state.music_dir = self.state.music_dir / "no-existe"
        app = LrcToolsApp(self.state)
        async with app.run_test(size=(100, 30)) as pilot:
            pilot.app.push_screen(TaskScreen("fetch", self.state))
            await pilot.pause(0.3)
            status = str(pilot.app.screen.query_one("#task-status", Static).render())
            self.assertIn("No se puede iniciar", status)


if __name__ == "__main__":
    unittest.main()
