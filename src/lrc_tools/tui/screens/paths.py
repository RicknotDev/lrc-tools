"""Paths configuration screen."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from lrc_tools import core
from lrc_tools.tui.dir_browser import DirectoryBrowserScreen


class PathsScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Volver"),
        Binding("ctrl+s", "save", "Guardar"),
        Binding("b", "browse", "Examinar"),
    ]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self):
        yield Header()
        yield Static("[bold #7aa2f7]Rutas[/]")
        yield Static("Carpeta de música (búsqueda recursiva):")
        yield Input(value=str(self.state.music_dir), id="music", classes="PathInput")
        yield Button("Examinar carpetas (b)", id="browse", variant="default")
        n = core.count_audio(self.state.music_dir)
        yield Static(f"[dim]Actual: {n} archivos de audio detectados[/]", id="audio-count")
        yield Static(f"[dim]Letras LRC (XDG):\n{core.LYRICS_RAW}\n\nLetras WLRC (XDG):\n{core.LYRICS_PROCESSED}[/]")
        yield Button("Guardar", id="save", variant="primary")
        yield Footer()

    def action_browse(self) -> None:
        self._open_browser()

    @on(Button.Pressed, "#browse")
    def browse_btn(self) -> None:
        self._open_browser()

    def _open_browser(self) -> None:
        start = Path(self.query_one("#music", Input).value.strip() or self.state.music_dir)

        def picked(path: Path | None) -> None:
            if path:
                self.query_one("#music", Input).value = str(path)
                self.query_one("#audio-count", Static).update(
                    f"[dim]Actual: {core.count_audio(path)} archivos de audio detectados[/]"
                )

        self.app.push_screen(DirectoryBrowserScreen(start), picked)

    def action_back(self) -> None:
        self.dismiss(None)

    def action_save(self) -> None:
        self._save()

    @on(Button.Pressed, "#save")
    def save_btn(self) -> None:
        self._save()

    def _save(self) -> None:
        raw = self.query_one("#music", Input).value.strip()
        path = core.normalize_path(raw)
        ok, msg = core.validate_music_dir(path)
        if not ok:
            self.app.notify(msg, severity="error")
            return
        self.state.music_dir = path
        core.ensure_lyrics_dirs()
        core.save_state(self.state)
        self.app.notify(f"Guardado · {core.count_audio(path)} archivos de audio")
        self.dismiss(True)
