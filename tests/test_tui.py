"""TUI smoke tests (require textual)."""

from __future__ import annotations

import unittest
from pathlib import Path

from lrc_tools import core


@unittest.skipUnless(core.textual_available(), "textual not installed")
class TestTuiSmoke(unittest.IsolatedAsyncioTestCase):
    async def test_app_mounts_main_menu(self) -> None:
        from lrc_tools.tui.app import LrcToolsApp

        app = LrcToolsApp(core.AppState(music_dir=Path.home()))
        async with app.run_test(size=(100, 40)) as pilot:
            self.assertTrue(pilot.app.is_running)
            menu = pilot.app.query("#menu")
            self.assertIsNotNone(menu)

    async def test_confirm_dialog_dismiss(self) -> None:
        from lrc_tools.tui.app import LrcToolsApp
        from lrc_tools.tui.widgets.confirm_dialog import ConfirmDialog

        app = LrcToolsApp()
        async with app.run_test() as pilot:
            pilot.app.push_screen(ConfirmDialog("\u00bfProbar?"))
            await pilot.pause()
            await pilot.click("#yes")
            await pilot.pause()


@unittest.skipUnless(core.textual_available(), "textual not installed")
class TestDirectoryBrowser(unittest.IsolatedAsyncioTestCase):
    async def test_browser_lists_home(self) -> None:
        from lrc_tools.tui.app import LrcToolsApp
        from lrc_tools.tui.dir_browser import DirectoryBrowserScreen

        app = LrcToolsApp()
        async with app.run_test() as pilot:
            pilot.app.push_screen(DirectoryBrowserScreen(Path.home()))
            await pilot.pause()
            dirs = pilot.app.query("#dirs")
            self.assertIsNotNone(dirs)


if __name__ == "__main__":
    unittest.main()
