"""Setup wizard — first-time configuration flow."""

from __future__ import annotations

import asyncio

from textual import work
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, RichLog, Static

from lrc_tools import core


class SetupWizard(Screen):
    BINDINGS = [Binding("escape", "back", "Volver")]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state
        self._step = 0

    def compose(self):
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
                code = await loop.run_in_executor(None, lambda: core.run_setup_script(on_line=w))
                if code != 0:
                    w(f"[red]setup.sh código {code}[/]")
                    return
            except FileNotFoundError as e:
                w(f"[red]{e}[/]")
                w("Definí LRC_TOOLS_REPO al repo clonado o instalá manualmente.")
                return
        else:
            w("[green]\u2713 lrc-fetch / processor / vis[/]")

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

        w("\n[bold]Paso 5/5[/] Process")
        try:
            cmd = core.process_cmd(self.state)
            code = await self._pipe(cmd, log)
        except FileNotFoundError as e:
            w(f"[red]{e}[/]")
            return

        core.save_state(self.state)
        wlrc = core.count_files(self.state.lyrics_processed, "*.wlrc")
        w(f"\n[green]\u2713 Setup listo — {wlrc} archivos .wlrc[/]")
        w("Usá [bold]Launch visualizer[/] o tecla [bold]v[/]")
        self.dismiss(True)

    async def _pipe(self, cmd: list[str], log: RichLog) -> int:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout
        while line := await proc.stdout.readline():
            text = line.decode(errors="replace").rstrip()
            if text:
                log.write(text)
        return await proc.wait()
