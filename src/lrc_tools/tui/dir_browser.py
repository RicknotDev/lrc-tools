"""Directory picker for music folder selection."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

from lrc_tools import core


class DirectoryBrowserScreen(Screen):
    """Navigate directories and pick a music folder."""

    def __init__(self, start: Path | None = None) -> None:
        super().__init__()
        start = start or Path.home() / "Music"
        self.current = (
            start.expanduser().resolve() if start.expanduser().exists() else Path.home()
        )
        self._shortcut_map: dict[str, Path] = {}
        self._dir_map: dict[str, Path] = {}

    BINDINGS = [
        Binding("escape", "cancel", "Cancelar"),
        Binding("enter", "select", "Seleccionar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold #7aa2f7]Elegir carpeta de música[/]", id="title")
        yield Static("", id="cwd")
        yield Static("[dim]Atajos rápidos[/]")
        yield ListView(id="shortcuts", classes="MenuList")
        yield Static("[dim]Subcarpetas · Enter selecciona · doble Enter entra[/]")
        yield ListView(id="dirs", classes="MenuList")
        with Vertical():
            yield Input(placeholder="Ruta manual…", id="manual")
            yield Button("Usar ruta escrita", id="manual-go", variant="primary")
            yield Button("Seleccionar carpeta actual", id="select-here", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        self._fill()

    def _fill(self) -> None:
        self.query_one("#cwd", Static).update(f"[cyan]{self.current}[/]")
        shortcuts = self.query_one("#shortcuts", ListView)
        shortcuts.clear()
        self._shortcut_map.clear()
        for index, p in enumerate(core.music_dir_candidates()):
            item_id = f"shortcut-{index}"
            self._shortcut_map[item_id] = p
            shortcuts.append(ListItem(Label(f"\U0001f4c1 {p}"), id=item_id))

        dirs = self.query_one("#dirs", ListView)
        dirs.clear()
        self._dir_map.clear()
        if self.current.parent != self.current:
            dirs.append(ListItem(Label("[bold]..[/]  (subir)"), id="up"))
        for index, sub in enumerate(core.list_subdirs(self.current)):
            item_id = f"dir-{index}"
            self._dir_map[item_id] = sub
            dirs.append(ListItem(Label(f"\U0001f4c1 {sub.name}"), id=item_id))

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_select(self) -> None:
        self._pick(self.current)

    def _pick(self, path: Path) -> None:
        ok, msg = core.validate_music_dir(path)
        if not ok:
            self.app.notify(msg, severity="error")
            return
        self.dismiss(path)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id == "up":
            self.current = self.current.parent
            self._fill()
            return
        if item_id in self._shortcut_map:
            self.current = self._shortcut_map[item_id]
            self._fill()
            return
        if item_id in self._dir_map:
            self.current = self._dir_map[item_id]
            self._fill()
            return

    @on(Button.Pressed, "#select-here")
    def select_here(self) -> None:
        self._pick(self.current)

    @on(Button.Pressed, "#manual-go")
    def manual_go(self) -> None:
        raw = self.query_one("#manual", Input).value.strip()
        if not raw:
            return
        path = core.normalize_path(raw)
        ok, msg = core.validate_music_dir(path)
        if not ok:
            self.app.notify(msg, severity="error")
            return
        self.dismiss(path)
