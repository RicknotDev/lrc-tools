"""Directory picker for music folder selection."""
from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

try:
    from lrc_tools import core
except ImportError:
    import core


class DirectoryBrowserScreen(Screen):
    """Navigate directories and pick a music folder."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancelar"),
        Binding("enter", "select", "Seleccionar"),
    ]

    def __init__(self, start: Path | None = None) -> None:
        super().__init__()
        start = start or Path.home() / "Music"
        self.current = start.expanduser().resolve() if start.expanduser().exists() else Path.home()

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
        for p in core.music_dir_candidates():
            shortcuts.append(
                ListItem(Label(f"📁 {p}"), id=f"shortcut:{p}")
            )

        dirs = self.query_one("#dirs", ListView)
        dirs.clear()
        if self.current.parent != self.current:
            dirs.append(ListItem(Label("[bold]..[/]  (subir)"), id="up"))
        for sub in core.list_subdirs(self.current):
            dirs.append(ListItem(Label(f"📁 {sub.name}"), id=f"dir:{sub}"))

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
        if item_id.startswith("shortcut:"):
            self.current = Path(item_id.split(":", 1)[1])
            self._fill()
            return
        if item_id.startswith("dir:"):
            self.current = Path(item_id.split(":", 1)[1])
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
