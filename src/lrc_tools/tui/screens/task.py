"""Task screen for running fetch, process or both (quick mode)."""

from __future__ import annotations

from collections.abc import Callable

from textual import work
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, RichLog, Static

from lrc_tools import core
from lrc_tools.tui.process_runner import CANCELLED, ProcessRunner, format_elapsed
from lrc_tools.tui.widgets.confirm_dialog import ConfirmDialog

Phase = tuple[str, Callable[[core.AppState], list[str]]]

TASKS: dict[str, tuple[str, list[Phase]]] = {
    "fetch": ("Descargar letras", [("Descargar", core.fetch_cmd)]),
    "process": ("Procesar letras", [("Procesar", core.process_cmd)]),
    "quick": ("Modo rápido · descargar + procesar", [("Descargar", core.fetch_cmd), ("Procesar", core.process_cmd)]),
}


class TaskScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Volver"),
        Binding("c", "cancel_task", "Cancelar tarea"),
        Binding("ctrl+l", "clear_log", "Limpiar log", show=False),
    ]

    def __init__(self, task_kind: str, state: core.AppState, *, ask_confirm: bool = True) -> None:
        super().__init__()
        if task_kind not in TASKS:
            raise ValueError(f"Unknown task: {task_kind!r}")
        self.task_kind = task_kind
        self.state = state
        self.ask_confirm = ask_confirm
        self.runner = ProcessRunner()
        self._phase_label = ""
        self._result: bool | None = None

    def compose(self):
        title, _ = TASKS[self.task_kind]
        yield Header()
        yield Static(f"[bold #7aa2f7]{title}[/]", id="task-title")
        yield Static("[dim]Preparando…[/]", id="task-status")
        yield RichLog(id="log", highlight=True, markup=True, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(1, self._tick)
        self._run_flow()

    # ── status line ────────────────────────────────────────────────
    def _set_status(self, text: str) -> None:
        self.query_one("#task-status", Static).update(text)

    def _tick(self) -> None:
        if self.runner.running:
            self._set_status(
                f"[#e0af68]● {self._phase_label}[/] · {format_elapsed(self.runner.elapsed)}"
                "  [dim]c = cancelar[/]"
            )

    # ── actions ────────────────────────────────────────────────────
    def action_back(self) -> None:
        if self.runner.running:
            self._confirm_leave()
        else:
            self.dismiss(self._result)

    def action_cancel_task(self) -> None:
        if self.runner.cancel():
            self.query_one("#log", RichLog).write("[yellow]Cancelando…[/]")
        else:
            self.app.notify("No hay ninguna tarea en curso", severity="warning", timeout=3)

    def action_clear_log(self) -> None:
        self.query_one("#log", RichLog).clear()

    @work(exclusive=True, group="leave")
    async def _confirm_leave(self) -> None:
        if await self.app.push_screen_wait(
            ConfirmDialog("La tarea sigue en curso.\n¿Cancelarla y volver al menú?", default_yes=False)
        ):
            self.runner.cancel()
            self.dismiss(None)

    # ── flow ───────────────────────────────────────────────────────
    def _confirm_message(self, stats: dict) -> str:
        if self.task_kind == "fetch":
            return f"¿Descargar letras para ~{stats['audio']} canciones?"
        if self.task_kind == "process":
            return f"¿Procesar {stats['lrc']} archivos .lrc a WLRC?"
        return f"¿Descargar letras para ~{stats['audio']} canciones y procesarlas?"

    def _precheck(self, stats: dict) -> str | None:
        """Return an error message when the task cannot start."""
        if self.task_kind in ("fetch", "quick") and not self.state.music_dir.is_dir():
            return f"La carpeta de música no existe: {self.state.music_dir}\nConfigurala en «Rutas» (tecla 7)."
        if self.task_kind == "process" and stats["lrc"] == 0:
            return "No hay .lrc en la carpeta raw. Ejecutá «Descargar letras» primero."
        return None

    @work(exclusive=True, group="task")
    async def _run_flow(self) -> None:
        log = self.query_one("#log", RichLog)
        stats = core.system_stats(self.state)

        problem = self._precheck(stats)
        if problem:
            self._set_status("[#f7768e]✗ No se puede iniciar[/]  [dim]Esc = volver[/]")
            log.write(f"[#f7768e]{problem}[/]")
            return

        if self.ask_confirm and not await self.app.push_screen_wait(ConfirmDialog(self._confirm_message(stats))):
            self.dismiss(None)
            return

        self.runner.columns = max(40, self.size.width - 4)
        _, phases = TASKS[self.task_kind]
        for index, (label, builder) in enumerate(phases, 1):
            self._phase_label = label if len(phases) == 1 else f"{label} ({index}/{len(phases)})"
            if len(phases) > 1:
                log.write(f"\n[bold cyan]── {self._phase_label} ──[/]")
            try:
                cmd = builder(self.state)
            except FileNotFoundError as e:
                self._finish(False, f"No se encontró la herramienta: {e}")
                return
            log.write(f"[dim]$ {' '.join(cmd)}[/]")
            self._tick()
            try:
                code = await self.runner.run(cmd, log.write)
            except OSError as e:
                self._finish(False, f"No se pudo ejecutar: {e}")
                return
            if code == CANCELLED:
                self._finish(False, "Tarea cancelada", cancelled=True)
                return
            if code != 0:
                self._finish(False, f"{label} terminó con código {code}")
                return

        core.save_state(self.state)
        self._finish(True, f"Completado en {format_elapsed(self.runner.elapsed)}")

    def _finish(self, ok: bool, message: str, *, cancelled: bool = False) -> None:
        self._result = ok
        log = self.query_one("#log", RichLog)
        if ok:
            log.write(f"\n[#9ece6a]✓ {message}[/]")
            self._set_status(f"[#9ece6a]✓ {message}[/]  [dim]Esc = volver[/]")
            self.app.notify(message, title=TASKS[self.task_kind][0], timeout=5)
        else:
            color = "#e0af68" if cancelled else "#f7768e"
            log.write(f"\n[{color}]✗ {message}[/]")
            self._set_status(f"[{color}]✗ {message}[/]  [dim]Esc = volver[/]")
