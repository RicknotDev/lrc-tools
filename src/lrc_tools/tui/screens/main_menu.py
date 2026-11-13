"""Main menu screen for lrc-tools TUI."""

from __future__ import annotations

from pathlib import Path

from textual import work
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, RichLog, Static

from lrc_tools import __version__, core
from lrc_tools.tui.song_picker import SongPickerScreen
from lrc_tools.tui.widgets.confirm_dialog import ConfirmDialog
from lrc_tools.tui.widgets.status_panel import StatusPanel

MENU_ITEMS = [
    ("1", "setup", "Asistente de setup", "Configuración inicial guiada"),
    ("2", "fetch", "Descargar letras", "Bajar .lrc desde LRCLIB"),
    ("3", "process", "Procesar letras", "Convertir .lrc → .wlrc"),
    ("4", "vis", "Visualizador", "Elegir canción y abrir lrc-vis"),
    ("5", "check", "Revisar letras", "Validar y reparar .lrc"),
    ("6", "download", "Descargar canciones", "Bajar canciones con spotdl"),
    ("7", "paths", "Rutas", "Carpeta de música y rutas XDG"),
    ("8", "deps", "Dependencias", "Ver e instalar dependencias"),
    ("9", "settings", "Ajustes", "config.yaml y opciones"),
    ("0", "delete_lyrics", "Borrar letras", "Eliminar todos los .lrc y .wlrc"),
    ("q", "exit", "Salir", ""),
]

QUICK_HINT = (
    "[dim]Enter elegir · números o letras como atajo · [/][bold]?[/][dim] todos los atajos[/]"
)


def _menu_label(key: str, title: str, desc: str) -> str:
    desc_part = f"  [dim]{desc}[/]" if desc else ""
    return f"[bold #e0af68]{key}[/]  [bold]{title:<20}[/]{desc_part}"


class MainMenu(Screen):
    BINDINGS = [
        Binding("f", "menu_fetch", "Descargar"),
        Binding("p", "menu_process", "Procesar"),
        Binding("v", "menu_vis", "Visualizar"),
        Binding("r", "quick_run", "Rápido"),
        Binding("q", "quit", "Salir"),
        Binding("1", "menu_setup", "Setup", show=False),
        Binding("2", "menu_fetch", "Fetch", show=False),
        Binding("3", "menu_process", "Process", show=False),
        Binding("4", "menu_vis", "Vis", show=False),
        Binding("5", "menu_check", "Revisar", show=False),
        Binding("6", "menu_download", "Download", show=False),
        Binding("7", "menu_paths", "Paths", show=False),
        Binding("8", "menu_deps", "Deps", show=False),
        Binding("9", "menu_settings", "Settings", show=False),
        Binding("0", "menu_delete_lyrics", "Delete all lyrics", show=False),
        Binding("c", "menu_check", "Revisar", show=False),
        Binding("d", "menu_download", "Download", show=False),
        Binding("l", "toggle_logs", "Logs", show=False),
        Binding("R", "refresh_status", "Actualizar", show=False),
    ]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.app_state = state
        self._logs_visible = False

    def compose(self):
        yield Header(show_clock=True)
        with Container(id="main-grid"):
            with Vertical(id="content"):
                yield Static(
                    f"[bold #7aa2f7]♪ lrc-tools[/] [dim]v{__version__} · letras sincronizadas en la terminal[/]",
                    id="banner",
                )
                yield Static(QUICK_HINT, classes="hint")
                items = [
                    ListItem(Label(_menu_label(key, title, desc)), id=action)
                    for key, action, title, desc in MENU_ITEMS
                ]
                yield ListView(*items, id="menu", classes="MenuList")
                with Container(id="log-panel", classes="hidden"):
                    yield RichLog(id="log", highlight=True, markup=True)
            yield StatusPanel(id="status-panel")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#menu", ListView).focus()
        self.query_one(StatusPanel).update("[dim]Cargando estado…[/]")
        self.refresh_sidebar()
        core.ensure_lyrics_dirs()
        core.ensure_config()
        self.set_interval(8, self.refresh_sidebar)
        if core.is_first_run():
            self.app.notify(
                "Primera vez: ejecutá «Asistente de setup» (tecla 1)",
                title="Bienvenido", timeout=10,
            )

    def action_refresh_status(self) -> None:
        self.refresh_sidebar()

    def refresh_sidebar(self) -> None:
        self._refresh_sidebar_worker()

    def _apply_sidebar_snapshot(self, snapshot: dict) -> None:
        self.query_one(StatusPanel).refresh_stats(self.app_state, snapshot)

    @work(thread=True, exclusive=True)
    def _refresh_sidebar_worker(self) -> None:
        snapshot = core.sidebar_snapshot(self.app_state)
        self.app.call_from_thread(self._apply_sidebar_snapshot, snapshot)

    def toggle_logs(self) -> None:
        panel = self.query_one("#log-panel")
        self._logs_visible = not self._logs_visible
        panel.set_class(not self._logs_visible, "hidden")

    def action_toggle_logs(self) -> None:
        self.toggle_logs()

    def append_log(self, line: str) -> None:
        log = self.query_one("#log", RichLog)
        if not self._logs_visible:
            self.toggle_logs()
        log.write(line)

    async def _confirm(self, msg: str, *, default_yes: bool = True) -> bool:
        return await self.app.push_screen_wait(ConfirmDialog(msg, default_yes=default_yes))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        action = event.item.id or ""
        if action == "exit":
            self.action_quit()
            return
        handlers = {
            "setup": self.action_menu_setup,
            "fetch": self.action_menu_fetch,
            "process": self.action_menu_process,
            "vis": self.action_menu_vis,
            "download": self.action_menu_download,
            "paths": self.action_menu_paths,
            "deps": self.action_menu_deps,
            "settings": self.action_menu_settings,
            "delete_lyrics": self.action_menu_delete_lyrics,
            "check": self.action_menu_check,
        }
        fn = handlers.get(action)
        if fn:
            fn()

    def action_menu_setup(self) -> None:
        from lrc_tools.tui.screens.setup_wizard import SetupWizard
        self.app.push_screen(SetupWizard(self.app_state), self._after_subscreen)

    def action_menu_fetch(self) -> None:
        from lrc_tools.tui.screens.task import TaskScreen
        self.app.push_screen(TaskScreen("fetch", self.app_state), self._after_subscreen)

    def action_menu_process(self) -> None:
        from lrc_tools.tui.screens.task import TaskScreen
        self.app.push_screen(TaskScreen("process", self.app_state), self._after_subscreen)

    def action_menu_vis(self) -> None:
        self._launch_vis()

    def action_menu_check(self) -> None:
        from lrc_tools.tui.screens.lyrics_check import LyricsCheckScreen
        self.app.push_screen(LyricsCheckScreen(self.app_state), self._after_subscreen)

    def action_menu_download(self) -> None:
        from lrc_tools.tui.screens.downloader import DownloaderScreen
        self.app.push_screen(DownloaderScreen(self.app_state), self._after_subscreen)

    def action_menu_paths(self) -> None:
        from lrc_tools.tui.screens.paths import PathsScreen
        self.app.push_screen(PathsScreen(self.app_state), self._after_subscreen)

    def action_menu_deps(self) -> None:
        from lrc_tools.tui.screens.deps import DepsScreen
        self.app.push_screen(DepsScreen(), self._after_subscreen)

    def action_menu_settings(self) -> None:
        from lrc_tools.tui.screens.settings import SettingsScreen
        self.app.push_screen(SettingsScreen(self.app_state), self._after_subscreen)

    def action_menu_delete_lyrics(self) -> None:
        self._delete_all_lyrics()

    @work(thread=False)
    async def _delete_all_lyrics(self) -> None:
        confirmed = await self._confirm(
            "\u00bfEliminar [bold]todos[/] los archivos .lrc y .wlrc?\n\nEsta acci\u00f3n no se puede deshacer.",
            default_yes=False,
        )
        if not confirmed:
            return
        lrc, wlrc = core.delete_all_lyrics(self.app_state)
        total = lrc + wlrc
        if total:
            self.app.notify(f"\u2713 Eliminados: {lrc} .lrc, {wlrc} .wlrc ({total} archivos)", timeout=5)
            self._after_subscreen(None)
        else:
            self.app.notify("No hab\u00eda archivos que eliminar", severity="warning")

    def action_quick_run(self) -> None:
        from lrc_tools.tui.screens.quick import QuickScreen
        self.app.push_screen(QuickScreen(self.app_state), self._after_subscreen)

    def _after_subscreen(self, _result) -> None:
        loaded = core.load_state()
        if loaded:
            self.app_state = loaded
        self.refresh_sidebar()

    def _launch_vis(self) -> None:
        if not core.count_files(self.app_state.lyrics_processed, "*.wlrc"):
            self.app.notify("No hay archivos .wlrc. Procesá letras primero.", severity="warning")
            return
        self.app.push_screen(SongPickerScreen(self.app_state), self._on_song_picked)

    def _on_song_picked(self, result: Path | None | bool) -> None:
        if result is False:
            return
        try:
            lrc_file = result if isinstance(result, Path) else None
            cmd = core.vis_cmd(self.app_state, lrc_file=lrc_file)
        except FileNotFoundError as e:
            self.app.notify(str(e), severity="error")
            return
        self.app.exit_launch = cmd  # type: ignore[attr-defined]
        self.app.reopen_picker = isinstance(result, Path)  # type: ignore[attr-defined]
        self.app.exit()

    def action_quit(self) -> None:
        self.app.exit()
