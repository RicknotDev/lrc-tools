"""Quick mode screen — fetch then process."""

from __future__ import annotations

import asyncio

from textual import work
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, RichLog, Static

from lrc_tools import core


class QuickScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Volver")]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self):
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
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
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
        log.write("\n[green]\u2713 Pipeline completo[/]")
        core.save_state(self.state)
        self.dismiss(True)
