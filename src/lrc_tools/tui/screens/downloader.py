"""Downloader screen — download songs via spotdl."""

from __future__ import annotations

import asyncio
import sys

from textual import on, work
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, RichLog, Static

from lrc_tools import core


class DownloaderScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Volver"),
        Binding("ctrl+s", "download", "Descargar"),
    ]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self):
        yield Header()
        yield Static("[bold #7aa2f7]Descargar canciones[/]")
        yield Static(
            "Pegá un link de Spotify / YouTube / playlist. Se descargará con spotdl en ~/Music.",
            classes="hint",
        )
        yield Input(placeholder="https://…", id="song-url")
        yield Static(f"[dim]Destino: {core.download_music_dir()}[/]")
        yield Button("Descargar", id="download", variant="primary")
        yield RichLog(id="log", highlight=True, markup=True)
        yield Footer()

    def action_back(self) -> None:
        self.dismiss(None)

    def action_download(self) -> None:
        self._start_download()

    @on(Button.Pressed, "#download")
    def download_btn(self) -> None:
        self._start_download()

    def _start_download(self) -> None:
        self._run_download()

    @work(exclusive=True)
    async def _run_download(self) -> None:
        log = self.query_one("#log", RichLog)
        url = self.query_one("#song-url", Input).value.strip()
        if not url:
            self.app.notify("Pegá un link primero", severity="warning")
            return

        if not core.command_exists("spotdl"):
            log.write("[yellow]spotdl no encontrado — instalando automáticamente…[/]")
            ok = await self._stream_cmd(log, self._spotdl_install_cmds())
            if not ok:
                log.write("[red]\u2717 No se pudo instalar spotdl[/]")
                self.app.notify("No se pudo instalar spotdl", severity="error")
                return
            log.write("[green]\u2713 spotdl instalado[/]\n")

        destination = core.download_music_dir()
        destination.mkdir(parents=True, exist_ok=True)
        self.state.music_dir = destination
        core.save_state(self.state)

        try:
            cmd = core.spotdl_cmd(url)
        except ValueError as e:
            self.app.notify(str(e), severity="error")
            return

        log.write(f"[bold]Descargando en[/] {destination}")
        log.write(f"[dim]{' '.join(cmd)}[/]\n")

        ok = await self._stream_cmd(log, [cmd])
        if ok:
            log.write("\n[green]\u2713 Descarga completada[/]")
            self.app.notify("Canción descargada en ~/Music")
        else:
            log.write("\n[red]\u2717 La descarga falló[/]")
            self.app.notify("La descarga falló", severity="error")

    def _spotdl_install_cmds(self) -> list[list[str]]:
        cmds: list[list[str]] = []
        if core.command_exists("pipx"):
            cmds.append(["pipx", "install", "spotdl"])
        cmds.append([sys.executable, "-m", "pip", "install", "spotdl", "--user"])
        if core.IS_WINDOWS:
            cmds.append([sys.executable, "-m", "pip", "install", "spotdl"])
        return cmds

    async def _stream_cmd(self, log: RichLog, cmds: list[list[str]]) -> bool:
        for cmd in cmds:
            log.write(f"[dim]{' '.join(cmd)}[/]")
            try:
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
                if await proc.wait() == 0:
                    return True
            except FileNotFoundError:
                log.write(f"[red]No se encontró: {cmd[0]}[/]")
                return False
        return False
