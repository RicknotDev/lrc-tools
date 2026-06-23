"""Settings screen for config.yaml management."""

from __future__ import annotations

from textual import on
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from lrc_tools import core


class SettingsScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Volver")]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self):
        yield Header()
        yield Static("[bold #7aa2f7]Configuración[/]")
        yield Static(f"[dim]{core.CONFIG_FILE}[/]")
        yield Static("", id="summary")
        onset = core.python_importable("librosa")
        yield Static(f"librosa: {'disponible' if onset else 'no instalado'}")
        yield Button("Regenerar config por defecto", id="regen", variant="warning")
        yield Button("Copiar ruta de config", id="open", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        s = core.config_summary()
        lines = [
            f"preserve_structure: [bold]{s.get('preserve_structure', '?')}[/]",
            f"search_threads:     {s.get('search_threads', '?')}",
            f"download_threads:   {s.get('download_threads', '?')}",
            f"use_onset_detection:{s.get('use_onset_detection', '?')}",
            f"default_font:       {s.get('default_font', '?')}",
        ]
        if s.get("_status") != "ok":
            lines.insert(0, f"[yellow]{s.get('_status')}[/]")
        self.query_one("#summary", Static).update("\n".join(lines))

    def action_back(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#regen")
    def regen(self) -> None:
        core.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        core.CONFIG_FILE.write_text(core.config_yaml(core.python_importable("librosa")), encoding="utf-8")
        self._refresh_summary()
        self.app.notify("config.yaml actualizado")

    @on(Button.Pressed, "#open")
    def open_cfg(self) -> None:
        core.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.app.notify(str(core.CONFIG_DIR), title="Config")
