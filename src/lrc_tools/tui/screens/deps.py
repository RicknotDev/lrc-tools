"""Dependency checker and installer screens."""

from __future__ import annotations

from textual import work
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, RichLog, Static

from lrc_tools import core


class DepsScreen(Screen):
    BINDINGS = [Binding("escape", "back", "Volver")]

    def compose(self):
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
            mark = "[green]\u2713[/]" if dep.present else "[red]\u2717[/]"
            crit = " [yellow](crítica)[/]" if dep.critical and not dep.present else ""
            lv.append(
                ListItem(Label(f"{mark} {dep.label}{crit}\n[dim]{dep.install_hint}[/]"), id=dep.key)
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

    def compose(self):
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
                write("[green]\u2713 OK[/]")
            else:
                write(f"[red]Código {code}[/]")
        except Exception as e:
            write(f"[red]{e}[/]")
