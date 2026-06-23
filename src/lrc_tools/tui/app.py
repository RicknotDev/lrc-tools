"""lrc-tools — Textual TUI main application."""

from __future__ import annotations

import sys

from textual.app import App
from textual.binding import Binding

from lrc_tools import core
from lrc_tools.tui.screens.main_menu import MainMenu

CSS = """
Screen {
    background: #0b1020;
    color: #dbe4ff;
}
Header {
    background: #11182d;
    color: #e5ecff;
    text-style: bold;
}
Footer {
    background: #0f1729;
    color: #b8c4e6;
}
#main-grid {
    layout: grid;
    grid-size: 2;
    grid-columns: 1fr 32;
    grid-gutter: 1 2;
    height: 1fr;
    padding: 1 2;
}
#content {
    height: 1fr;
    padding: 0 1 1 1;
}
#content > Static:first-child {
    margin-bottom: 1;
}
#status-panel {
    background: #11182d;
    border: round #355070;
    padding: 1 2;
    height: 1fr;
}
#status-panel Static {
    margin-bottom: 0;
}
.status-title {
    text-style: bold;
    color: #8ec5ff;
    margin-bottom: 1;
}
.status-ok { color: #9fe870; }
.status-warn { color: #ffd166; }
.status-err { color: #ff7b7b; }
ListView, MenuList {
    background: #11182d;
    border: round #355070;
    padding: 0 1;
    height: auto;
    max-height: 1fr;
}
ListView > ListItem, MenuList > ListItem {
    padding: 0 1;
    height: 3;
    margin: 0 0 1 0;
}
ListView > ListItem.--highlight, MenuList > ListItem.--highlight {
    background: #1c2742;
    color: #f7fbff;
    border-left: tall #7aa2f7;
}
Button {
    background: #1b2640;
    color: #eaf1ff;
    border: round #44648c;
    margin-top: 1;
}
Button.-primary, Button.-success, Button.-warning { text-style: bold; }
Input {
    background: #0f1729;
    border: round #44648c;
    color: #eaf1ff;
    margin: 1 0;
    padding: 0 1;
}
RichLog {
    background: #0a1120;
    border: round #355070;
    color: #dbe4ff;
}
#log-panel {
    height: 1fr;
    background: transparent;
    margin-top: 1;
}
#log-panel RichLog { height: 1fr; }
.hint { color: #7f8db3; margin: 1 0; }
.hidden { display: none; }
Dialog { align: center middle; }
#dialog {
    width: 64;
    height: auto;
    background: #11182d;
    border: round #7aa2f7;
    padding: 1 2;
}
#dialog-buttons {
    layout: horizontal;
    height: auto;
    margin-top: 1;
}
#dialog-buttons Button { margin-right: 1; }
PathInput { margin: 1 0; }
"""


class LrcToolsApp(App):
    CSS = CSS
    TITLE = "lrc-tools"
    SUB_TITLE = "terminal lyrics"

    BINDINGS = [Binding("question_mark", "help", "Ayuda")]

    def __init__(self, state: core.AppState | None = None, *, quick: bool = False, reopen_picker: bool = False) -> None:
        super().__init__()
        self.state = state or core.default_state()
        self.exit_launch: list[str] | None = None
        self.reopen_picker: bool = False
        self._quick = quick
        self._reopen_picker = reopen_picker

    def on_mount(self) -> None:
        menu = MainMenu(self.state)
        self.push_screen(menu)
        if self._quick:
            from lrc_tools.tui.screens.quick import QuickScreen
            self.push_screen(QuickScreen(self.state))
        elif self._reopen_picker:
            self.call_after_refresh(menu.action_menu_vis)

    def action_help(self) -> None:
        from lrc_tools.tui.screens.main_menu import QUICK_HINT
        self.notify(QUICK_HINT, timeout=8)


def run_tui(*, quick: bool = False) -> int:
    if not core.textual_available():
        print("Falta Textual. Instalá con:\n"
              f"  {sys.executable} -m pip install textual", file=sys.stderr)
        return 1

    import subprocess

    state = core.default_state()
    core.ensure_lyrics_dirs()
    reopen_picker = False

    while True:
        app = LrcToolsApp(state, quick=quick, reopen_picker=reopen_picker)
        app.run()
        launch = getattr(app, "exit_launch", None)
        if not launch:
            return 0

        result = subprocess.run(launch)
        reopen_picker = bool(getattr(app, "reopen_picker", False) and result.returncode == 10)
        quick = False
        if not reopen_picker:
            return result.returncode


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="lrc-tools TUI")
    parser.add_argument("--quick", "-r", action="store_true", help="Modo rápido: fetch + process")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        print("Se requiere Python 3.12+", file=sys.stderr)
        sys.exit(1)
    sys.exit(run_tui(quick=args.quick))


if __name__ == "__main__":
    main()
