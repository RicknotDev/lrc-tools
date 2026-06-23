"""Task screen for running fetch or process."""

from __future__ import annotations

import asyncio

from textual import work
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, RichLog, Static

from lrc_tools import core
from lrc_tools.tui.widgets.confirm_dialog import ConfirmDialog


class TaskScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Volver")]

    def __init__(self, task_kind: str, state: core.AppState) -> None:
        super().__init__()
        self.task_kind = task_kind
        self.state = state

    def compose(self):
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
            msg = f"\u00bfDescargar letras para ~{stats['audio']} canciones?"
        else:
            msg = f"\u00bfProcesar {stats['lrc']} archivos .lrc a WLRC?"

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
                log.write("\n[green]\u2713 Completado[/]")
                core.save_state(self.state)
            else:
                log.write(f"\n[red]\u2717 Código de salida {code}[/]")
        except FileNotFoundError as e:
            log.write(f"[red]{e}[/]")
        except Exception as e:
            log.write(f"[red]Error: {e}[/]")

    async def _stream(self, cmd: list[str], log: RichLog) -> int:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
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
