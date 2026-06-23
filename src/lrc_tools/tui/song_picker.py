"""Pick a song before launching the visualizer."""

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from lrc_tools import core


class SongPickerScreen(Screen):
    """Choose a .wlrc track or follow the player automatically."""

    BINDINGS = [
        Binding("escape", "cancel", "Volver"),
        Binding("a", "pick_auto", "Automático"),
        Binding("delete", "delete_song", "Borrar"),
        Binding("d", "delete_song", "Borrar", show=False),
    ]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state
        self._all_tracks: list[core.TrackEntry] = []
        self._id_to_path: dict[str, Path] = {}
        self._auto_item_id = "auto-0"
        self._rebuild_serial = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold #7aa2f7]Elegir canción para el visualizador[/]")
        yield Static(
            "[dim]Enter = lanzar \u00b7 a = automático (playerctl) \u00b7 ESC = volver[/]",
            classes="hint",
        )
        yield Input(placeholder="Buscar por nombre…", id="filter")
        yield Static("", id="count")
        yield ListView(id="songs", classes="MenuList")
        yield Footer()

    def on_mount(self) -> None:
        self._all_tracks = core.list_tracks(self.state.lyrics_processed)
        self._rebuild_list("")
        self.query_one("#filter", Input).focus()

    def _rebuild_list(self, query: str) -> None:
        lv = self.query_one("#songs", ListView)
        lv.clear()
        self._id_to_path.clear()
        self._rebuild_serial += 1
        serial = self._rebuild_serial
        self._auto_item_id = f"auto-{serial}"

        lv.append(
            ListItem(
                Label("[bold #9ece6a]\u25c9 Automático[/]\n[dim]Seguir lo que suena en el reproductor[/]"),
                id=self._auto_item_id,
            )
        )
        q = query.strip().lower()
        shown = 0
        for entry in self._all_tracks:
            if q and q not in entry.label.lower():
                continue
            item_id = f"track-{serial}-{shown}"
            self._id_to_path[item_id] = entry.path
            lv.append(ListItem(Label(f"\u266a {entry.label}"), id=item_id))
            shown += 1
        total = len(self._all_tracks)
        self.query_one("#count", Static).update(
            f"[dim]{shown} de {total} canciones[/]" if q else f"[dim]{total} canciones con letra[/]"
        )

    @on(Input.Changed, "#filter")
    def filter_changed(self, event: Input.Changed) -> None:
        self._rebuild_list(event.value)

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_pick_auto(self) -> None:
        self.dismiss(None)

    def action_delete_song(self) -> None:
        lv = self.query_one("#songs", ListView)
        highlighted = lv.highlighted_child
        if not highlighted or not highlighted.id:
            return
        item_id = highlighted.id
        if item_id.startswith("auto-"):
            self.app.notify("No se puede borrar la opción automática", severity="warning")
            return
        path = self._id_to_path.get(item_id)
        if not path:
            return
        self._confirm_and_delete(path)

    @work(thread=False)
    async def _confirm_and_delete(self, path: Path) -> None:
        from lrc_tools.tui.widgets.confirm_dialog import ConfirmDialog

        confirmed = await self.app.push_screen_wait(
            ConfirmDialog(f"¿Borrar [bold]{path.stem}[/] y su archivo .lrc correspondiente?")
        )
        if confirmed:
            deleted = core.delete_track(self.state, path)
            if deleted:
                self.app.notify(f"✓ Eliminado: {path.stem}", timeout=3)
                self._all_tracks = core.list_tracks(self.state.lyrics_processed)
                filter_input = self.query_one("#filter", Input).value or ""
                self._rebuild_list(filter_input)
            else:
                self.app.notify("No se encontraron archivos para borrar", severity="warning")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id == self._auto_item_id:
            self.dismiss(None)
            return
        path = self._id_to_path.get(item_id)
        if path and path.is_file():
            self.dismiss(path)
        else:
            self.app.notify("Archivo no encontrado", severity="error")
