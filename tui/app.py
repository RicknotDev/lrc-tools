"""
lrc-tools — Textual TUI
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
)

try:
    from lrc_tools import core
    from lrc_tools.tui.dir_browser import DirectoryBrowserScreen
    from lrc_tools.tui.song_picker import SongPickerScreen
except ImportError:
    import core
    from tui.dir_browser import DirectoryBrowserScreen
    from tui.song_picker import SongPickerScreen

BANNER = r"""
[bold #7aa2f7]
  _      ____   ___    _____           _
 | |    |___ \ / _ \  |_   _|_ _  ___| |_
 | |      __) | | | |   | |/ _` |/ _ \ __|
 | |___  / __/| |_| |   | | (_| |  __/ |_
 |_____|_____| \___/    |_|\_\__,_|\___|\__|
[/]
[dim]Letras sincronizadas · TUI[/]
"""

CSS = """
Screen {
    background: #0d0e14;
}

#main-grid {
    layout: grid;
    grid-size: 2;
    grid-columns: 1fr 28;
    height: 1fr;
}

#content {
    height: 1fr;
    padding: 0 1;
}

#status-panel {
    background: #16161e;
    border-left: tall #24283b;
    padding: 1;
    height: 1fr;
}

#status-panel Static {
    margin-bottom: 0;
}

.status-title {
    text-style: bold;
    color: #7aa2f7;
    margin-bottom: 1;
}

.status-ok { color: #9ece6a; }
.status-warn { color: #e0af68; }
.status-err { color: #f7768e; }

MenuList {
    background: #16161e;
    border: tall #24283b;
    padding: 0 1;
    height: auto;
    max-height: 1fr;
}

MenuList > ListItem {
    padding: 0 1;
    height: 3;
}

MenuList > ListItem.--highlight {
    background: #24283b;
}

#log-panel {
    height: 1fr;
    border: tall #24283b;
    background: #0d0e14;
    margin-top: 1;
}

#log-panel RichLog {
    height: 1fr;
}

.hint {
    color: #565f89;
    margin-top: 1;
}

.hidden {
    display: none;
}

Dialog {
    align: center middle;
}

#dialog {
    width: 60;
    height: auto;
    background: #16161e;
    border: tall #7aa2f7;
    padding: 1 2;
}

#dialog-buttons {
    layout: horizontal;
    height: auto;
    margin-top: 1;
}

#dialog-buttons Button {
    margin-right: 1;
}

PathInput {
    margin: 1 0;
}
"""


MENU_ITEMS = [
    ("1", "setup", "Asistente de setup", "Configuración inicial guiada"),
    ("2", "fetch", "Fetch lyrics", "Descargar .lrc desde LRCLIB"),
    ("3", "process", "Process lyrics", "Convertir .lrc → .wlrc"),
    ("4", "vis", "Launch visualizer", "Elegir canción y abrir lrc-vis"),
    ("5", "paths", "Configure paths", "Carpeta de música y rutas XDG"),
    ("6", "deps", "Dependency checker", "Ver e instalar dependencias"),
    ("7", "settings", "Settings", "config.yaml y opciones"),
    ("q", "exit", "Exit", "Salir"),
]

QUICK_HINT = (
    "[dim]Atajos: [/][bold]1-7[/] menú · [bold]f[/] fetch · [bold]p[/] process · "
    "[bold]v[/] vis · [bold]r[/] rápido (fetch+process) · [bold]l[/] logs · [bold]q[/] salir"
)


class ConfirmDialog(ModalScreen[bool]):
    """Y/N confirmation."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }
    """

    def __init__(self, message: str, *, default_yes: bool = True) -> None:
        super().__init__()
        self.message = message
        self.default_yes = default_yes

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Static(self.message)
            with Horizontal(id="dialog-buttons"):
                yield Button("Sí (Y)", id="yes", variant="success")
                yield Button("No (N)", id="no", variant="default")

    def on_mount(self) -> None:
        self.call_after_refresh(self._focus_default)

    def _focus_default(self) -> None:
        btn_id = "yes" if self.default_yes else "no"
        self.query_one(f"#{btn_id}", Button).focus()

    @on(Button.Pressed, "#yes")
    def yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def no(self) -> None:
        self.dismiss(False)

    def key_y(self) -> None:
        self.dismiss(True)

    def key_n(self) -> None:
        self.dismiss(False)


class StatusPanel(Static):
    """Sidebar with live system stats."""

    def refresh_stats(self, state: core.AppState) -> None:
        stats = core.system_stats(state)
        deps = core.scan_dependencies()
        missing = [d.label for d in deps if not d.present and d.critical]
        tools = "✓" if stats["tools"] else "✗"
        deps_s = "✓" if stats["deps_ok"] else "✗"
        music = stats["music_dir"]
        if len(music) > 22:
            music = "…" + music[-21:]

        lines = [
            "[bold #7aa2f7]Estado[/]",
            "",
            f"Música [dim]{music}[/]",
            f"Canciones  [bold]{stats['audio']}[/]",
            f".lrc       [bold]{stats['lrc']}[/]",
            f".wlrc      [bold]{stats['wlrc']}[/]",
            "",
            f"Herramientas {tools}",
            f"Deps críticas {deps_s}",
        ]
        if missing:
            lines.append(f"[#f7768e]Falta: {', '.join(missing[:2])}[/]")
        lines.extend([
            "",
            "[dim]XDG raw[/]",
            f"[dim]{core.LYRICS_RAW}[/]",
            "[dim]XDG out[/]",
            f"[dim]{core.LYRICS_PROCESSED}[/]",
        ])
        self.update("\n".join(lines))


class MainMenu(Screen):
    """Home screen with menu + optional log drawer."""

    BINDINGS = [
        Binding("q", "quit", "Salir"),
        Binding("1", "menu_setup", "Setup", show=False),
        Binding("2", "menu_fetch", "Fetch", show=False),
        Binding("3", "menu_process", "Process", show=False),
        Binding("4", "menu_vis", "Vis", show=False),
        Binding("5", "menu_paths", "Paths", show=False),
        Binding("6", "menu_deps", "Deps", show=False),
        Binding("7", "menu_settings", "Settings", show=False),
        Binding("f", "menu_fetch", "Fetch", show=False),
        Binding("p", "menu_process", "Process", show=False),
        Binding("v", "menu_vis", "Vis", show=False),
        Binding("r", "quick_run", "Rápido", show=False),
        Binding("l", "toggle_logs", "Logs", show=False),
        Binding("R", "refresh_status", "Actualizar", show=False),
    ]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.app_state = state
        self._logs_visible = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-grid"):
            with Vertical(id="content"):
                yield Static(BANNER)
                yield Static(QUICK_HINT, classes="hint")
                items = [
                    ListItem(
                        Label(
                            f"[bold]{title}[/]  [dim]({key})[/]\n{desc}",
                        ),
                        id=action,
                    )
                    for key, action, title, desc in MENU_ITEMS
                ]
                yield ListView(*items, id="menu", classes="MenuList")
                with Container(id="log-panel", classes="hidden"):
                    yield RichLog(id="log", highlight=True, markup=True)
            yield StatusPanel(id="status", classes="status-panel")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#menu", ListView).focus()
        self.refresh_sidebar()
        core.ensure_lyrics_dirs()
        core.ensure_config()
        self.set_interval(5, self.refresh_sidebar)
        if core.is_first_run():
            self.app.notify(
                "Primera vez: ejecutá «Asistente de setup» (tecla 1)",
                title="Bienvenido",
                timeout=10,
            )

    def action_refresh_status(self) -> None:
        self.refresh_sidebar()

    def refresh_sidebar(self) -> None:
        self.query_one(StatusPanel).refresh_stats(self.app_state)

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
            "paths": self.action_menu_paths,
            "deps": self.action_menu_deps,
            "settings": self.action_menu_settings,
        }
        fn = handlers.get(action)
        if fn:
            fn()

    def action_menu_setup(self) -> None:
        self.app.push_screen(SetupWizard(self.app_state), self._after_subscreen)

    def action_menu_fetch(self) -> None:
        self.app.push_screen(TaskScreen("fetch", self.app_state), self._after_subscreen)

    def action_menu_process(self) -> None:
        self.app.push_screen(TaskScreen("process", self.app_state), self._after_subscreen)

    def action_menu_vis(self) -> None:
        self._launch_vis()

    def action_menu_paths(self) -> None:
        self.app.push_screen(PathsScreen(self.app_state), self._after_subscreen)

    def action_menu_deps(self) -> None:
        self.app.push_screen(DepsScreen(), self._after_subscreen)

    def action_menu_settings(self) -> None:
        self.app.push_screen(SettingsScreen(self.app_state), self._after_subscreen)

    def action_quick_run(self) -> None:
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
        self.app.exit()

    def action_quit(self) -> None:
        self.app.exit()


class TaskScreen(Screen):
    """Run fetch or process with live log."""

    BINDINGS = [
        Binding("escape", "back", "Volver"),
    ]

    def __init__(self, task_kind: str, state: core.AppState) -> None:
        super().__init__()
        self.task_kind = task_kind
        self.state = state

    def compose(self) -> ComposeResult:
        title = "Descargar letras" if self.task_kind == "fetch" else "Procesar letras"
        yield Header()
        yield Static(f"[bold #7aa2f7]{title}[/]", id="task-title")
        yield RichLog(id="log", highlight=True, markup=True)
        yield Static("[dim]ESC para volver · Ctrl+C cancela tarea[/]", classes="hint")
        yield Footer()

    def on_mount(self) -> None:
        self._run_flow()

    def action_back(self) -> None:
        self.dismiss(None)

    @work(exclusive=True)
    async def _run_flow(self) -> None:
        log = self.query_one("#log", RichLog)
        stats = core.system_stats(self.state)

        if self.task_kind == "fetch":
            msg = f"¿Descargar letras para ~{stats['audio']} canciones?"
        else:
            msg = f"¿Procesar {stats['lrc']} archivos .lrc a WLRC?"

        if not await self.app.push_screen_wait(ConfirmDialog(msg)):
            self.dismiss(None)
            return

        log.write("[dim]Iniciando…[/]")

        try:
            if self.task_kind == "fetch":
                if not self.state.music_dir.is_dir():
                    log.write("[red]La carpeta de música no existe.[/]")
                    return
                log.write(f"[cyan]Audio: {stats['audio']} archivos[/]")
                cmd = core.fetch_cmd(self.state)
                log.write(f"[dim]{' '.join(cmd)}[/]\n")
                code = await self._stream(cmd, log)
            else:
                if stats["lrc"] == 0:
                    log.write("[yellow]No hay .lrc en raw. Ejecutá Fetch primero.[/]")
                    return
                log.write(f"[cyan].lrc: {stats['lrc']} archivos[/]")
                cmd = core.process_cmd(self.state)
                log.write(f"[dim]{' '.join(cmd)}[/]\n")
                code = await self._stream(cmd, log)

            if code == 0:
                log.write("\n[green]✓ Completado[/]")
                core.save_state(self.state)
            else:
                log.write(f"\n[red]✗ Código de salida {code}[/]")
        except FileNotFoundError as e:
            log.write(f"[red]{e}[/]")
        except Exception as e:
            log.write(f"[red]Error: {e}[/]")

    async def _stream(self, cmd: list[str], log: RichLog) -> int:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text = line.decode(errors="replace").rstrip()
            if text:
                log.write(text)
        return await proc.wait()


class QuickScreen(Screen):
    """Advanced: fetch then process."""

    BINDINGS = [Binding("escape", "back", "Volver")]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold #7aa2f7]Modo rápido[/] — fetch + process")
        yield RichLog(id="log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self._run_pipeline()

    def action_back(self) -> None:
        self.dismiss(None)

    @work(exclusive=True)
    async def _run_pipeline(self) -> None:
        log = self.query_one("#log", RichLog)

        for phase, builder in (
            ("FETCH", core.fetch_cmd),
            ("PROCESS", core.process_cmd),
        ):
            log.write(f"\n[bold cyan]=== {phase} ===[/]\n")
            try:
                cmd = builder(self.state)
            except FileNotFoundError as e:
                log.write(f"[red]{e}[/]")
                return
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            assert proc.stdout
            while line := await proc.stdout.readline():
                text = line.decode(errors="replace").rstrip()
                if text:
                    log.write(text)
            code = await proc.wait()
            if code != 0:
                log.write(f"[red]{phase} falló ({code})[/]")
                return
        log.write("\n[green]✓ Pipeline completo[/]")
        core.save_state(self.state)
        self.dismiss(True)


class PathsScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Volver"),
        Binding("ctrl+s", "save", "Guardar"),
        Binding("b", "browse", "Examinar"),
    ]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold #7aa2f7]Rutas[/]")
        yield Static("Carpeta de música (búsqueda recursiva):")
        yield Input(value=str(self.state.music_dir), id="music", classes="PathInput")
        yield Button("Examinar carpetas (b)", id="browse", variant="default")
        n = core.count_audio(self.state.music_dir)
        yield Static(f"[dim]Actual: {n} archivos de audio detectados[/]", id="audio-count")
        yield Static(
            f"[dim]Letras LRC (XDG):\n{core.LYRICS_RAW}\n\n"
            f"Letras WLRC (XDG):\n{core.LYRICS_PROCESSED}[/]"
        )
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


class DepsScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Volver")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold #7aa2f7]Dependencias[/]")
        yield ListView(id="dep-list", classes="MenuList")
        yield Static("[dim]Enter instalar · ESC volver[/]", classes="hint")
        yield Footer()

    def on_mount(self) -> None:
        self._rebuild()

    def _rebuild(self) -> None:
        lv = self.query_one("#dep-list", ListView)
        lv.clear()
        for dep in core.scan_dependencies():
            mark = "[green]✓[/]" if dep.present else "[red]✗[/]"
            crit = " [yellow](crítica)[/]" if dep.critical and not dep.present else ""
            lv.append(
                ListItem(
                    Label(f"{mark} {dep.label}{crit}\n[dim]{dep.install_hint}[/]"),
                    id=dep.key,
                )
            )

    def action_back(self) -> None:
        self.dismiss(None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        key = event.item.id
        dep = next((d for d in core.scan_dependencies() if d.key == key), None)
        if not dep or dep.present or not dep.install_cmd:
            if dep and dep.present:
                self.app.notify(f"{dep.label} ya está instalado")
            return

        def done(_):
            self._rebuild()

        self.app.push_screen(InstallScreen(dep), done)


class InstallScreen(Screen):
    def __init__(self, dep: core.Dependency) -> None:
        super().__init__()
        self.dep = dep

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Instalando [bold]{self.dep.label}[/]")
        yield RichLog(id="log", highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        self._run()

    @work(thread=True)
    def _run(self) -> None:
        log = self.query_one("#log", RichLog)
        cmd = self.dep.install_cmd
        if not cmd:
            return

        def write(line: str) -> None:
            self.app.call_from_thread(log.write, line)

        write(f"[dim]{' '.join(cmd)}[/]")
        try:
            code = core.run_command(cmd, on_line=write)
            if code == 0:
                write("[green]✓ OK[/]")
            else:
                write(f"[red]Código {code}[/]")
        except Exception as e:
            write(f"[red]{e}[/]")


class SettingsScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Volver")]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
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
        core.CONFIG_FILE.write_text(
            core.config_yaml(core.python_importable("librosa")),
            encoding="utf-8",
        )
        self._refresh_summary()
        self.app.notify("config.yaml actualizado")

    @on(Button.Pressed, "#open")
    def open_cfg(self) -> None:
        core.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.app.notify(str(core.CONFIG_DIR), title="Config")


class SetupWizard(Screen):
    """Full first-time setup."""

    BINDINGS = [Binding("escape", "back", "Volver")]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state
        self._step = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold #7aa2f7]Asistente de setup[/]", id="wiz-title")
        yield RichLog(id="log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self._run_wizard()

    def action_back(self) -> None:
        self.dismiss(None)

    @work(exclusive=True)
    async def _run_wizard(self) -> None:
        log = self.query_one("#log", RichLog)

        def w(line: str) -> None:
            log.write(line)

        w("[bold]Paso 1/5[/] Dependencias críticas")
        for dep in core.scan_dependencies():
            if dep.present or not dep.critical:
                continue
            w(f"[yellow]Falta {dep.label}[/] — instalá desde «Dependency checker»")
        if not core.critical_deps_ok():
            w("[red]Completá dependencias antes de continuar.[/]")
            return

        w("\n[bold]Paso 2/5[/] Herramientas CLI")
        if not core.tools_installed():
            w("Ejecutando setup.sh…")
            try:
                loop = asyncio.get_running_loop()
                code = await loop.run_in_executor(
                    None,
                    lambda: core.run_setup_script(on_line=w),
                )
                if code != 0:
                    w(f"[red]setup.sh código {code}[/]")
                    return
            except FileNotFoundError as e:
                w(f"[red]{e}[/]")
                w("Definí LRC_TOOLS_REPO al repo clonado o instalá manualmente.")
                return
        else:
            w("[green]✓ lrc-fetch / processor / vis[/]")

        w("\n[bold]Paso 3/5[/] Carpetas XDG")
        core.ensure_lyrics_dirs()
        core.ensure_config()
        w(f"  raw: {core.LYRICS_RAW}")
        w(f"  out: {core.LYRICS_PROCESSED}")

        if not self.state.music_dir.is_dir():
            w(f"[yellow]Música no encontrada: {self.state.music_dir}[/]")
            w("Configurá la ruta en «Configure paths».")
            return

        w(f"\n[bold]Paso 4/5[/] Fetch ({core.count_audio(self.state.music_dir)} temas)")
        try:
            cmd = core.fetch_cmd(self.state)
            code = await self._pipe(cmd, log)
            if code != 0:
                w("[yellow]Fetch con errores; podés reintentar después.[/]")
        except FileNotFoundError as e:
            w(f"[red]{e}[/]")
            return

        w(f"\n[bold]Paso 5/5[/] Process")
        try:
            cmd = core.process_cmd(self.state)
            code = await self._pipe(cmd, log)
        except FileNotFoundError as e:
            w(f"[red]{e}[/]")
            return

        core.save_state(self.state)
        wlrc = core.count_files(self.state.lyrics_processed, "*.wlrc")
        w(f"\n[green]✓ Setup listo — {wlrc} archivos .wlrc[/]")
        w("Usá [bold]Launch visualizer[/] o tecla [bold]v[/]")
        self.dismiss(True)

    async def _pipe(self, cmd: list[str], log: RichLog) -> int:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout
        while line := await proc.stdout.readline():
            text = line.decode(errors="replace").rstrip()
            if text:
                log.write(text)
        return await proc.wait()


class LrcToolsApp(App):
    """Main application."""

    CSS = CSS
    TITLE = "lrc-tools"
    SUB_TITLE = "terminal lyrics"

    BINDINGS = [
        Binding("question_mark", "help", "Ayuda"),
    ]

    def __init__(self, state: core.AppState | None = None, *, quick: bool = False) -> None:
        super().__init__()
        self.state = state or core.default_state()
        self.exit_launch: list[str] | None = None
        self._quick = quick

    def on_mount(self) -> None:
        self.push_screen(MainMenu(self.state))
        if self._quick:
            self.push_screen(QuickScreen(self.state))

    def action_help(self) -> None:
        self.notify(QUICK_HINT, timeout=8)


def run_tui(*, quick: bool = False) -> int:
    if not core.textual_available():
        print(
            "Falta Textual. Instalá con:\n"
            f"  {sys.executable} -m pip install textual --break-system-packages",
            file=sys.stderr,
        )
        return 1

    state = core.default_state()
    core.ensure_lyrics_dirs()

    app = LrcToolsApp(state, quick=quick)
    app.run()
    launch = getattr(app, "exit_launch", None)
    if launch:
        os.execvp(launch[0], launch)
    return 0


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="lrc-tools TUI")
    parser.add_argument(
        "--quick", "-r", action="store_true", help="Modo rápido: fetch + process"
    )
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        print("Se requiere Python 3.12+", file=sys.stderr)
        sys.exit(1)
    sys.exit(run_tui(quick=args.quick))
