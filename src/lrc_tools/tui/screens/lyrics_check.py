"""Validate downloaded .lrc files and repair the broken ones."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from textual import on, work
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from lrc_tools import core
from lrc_tools.parser import repair_lrc, validate_lrc
from lrc_tools.tui.widgets.confirm_dialog import ConfirmDialog

# Problems repair_lrc() can actually fix (it drops duplicates, comments out junk
# lines and re-sorts). "No timestamped lyric lines" means plain lyrics: not fixable.
_UNFIXABLE = ("No timestamped lyric lines found", "Empty file", "Cannot read file")


@dataclass
class FileReport:
    path: Path
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    @property
    def fixable(self) -> bool:
        return bool(self.problems) and not any(p.startswith(_UNFIXABLE) for p in self.problems)


def scan_lyrics(folder: Path) -> list[FileReport]:
    reports = [FileReport(p, validate_lrc(p)) for p in sorted(folder.rglob("*.lrc"))]
    # Problems first, then alphabetical.
    return sorted(reports, key=lambda r: (r.ok, r.path.name.lower()))


def repair_reports(reports: list[FileReport]) -> tuple[int, int]:
    """Back up and repair every fixable report. Returns (files_repaired, issues_fixed)."""
    files = issues = 0
    for report in reports:
        if not report.fixable:
            continue
        core.backup_file(report.path)
        issues += max(repair_lrc(report.path), 0)
        files += 1
    return files, issues


class LyricsCheckScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Volver"),
        Binding("r", "repair", "Reparar"),
        Binding("s", "rescan", "Re-escanear"),
    ]

    def __init__(self, state: core.AppState) -> None:
        super().__init__()
        self.state = state
        self.reports: list[FileReport] = []

    def compose(self):
        yield Header()
        yield Static("[bold #7aa2f7]Revisar letras[/] [dim]· valida los .lrc descargados[/]")
        yield Static("[dim]Escaneando…[/]", id="check-summary")
        yield DataTable(id="check-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="check-detail", classes="hint")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#check-table", DataTable)
        table.add_columns("Estado", "Problemas", "Archivo")
        self._scan()

    def action_back(self) -> None:
        self.dismiss(None)

    def action_rescan(self) -> None:
        self._scan()

    @work(thread=True, exclusive=True)
    def _scan(self) -> None:
        reports = scan_lyrics(self.state.lyrics_raw)
        self.app.call_from_thread(self._show, reports)

    def _show(self, reports: list[FileReport]) -> None:
        self.reports = reports
        table = self.query_one("#check-table", DataTable)
        table.clear()
        for i, report in enumerate(reports):
            if report.ok:
                status = "[#9ece6a]✓ ok[/]"
            elif report.fixable:
                status = "[#e0af68]⚠ reparable[/]"
            else:
                status = "[#f7768e]✗ sin sincronía[/]"
            table.add_row(status, str(len(report.problems)) if report.problems else "", report.path.stem, key=str(i))

        bad = [r for r in reports if not r.ok]
        fixable = [r for r in reports if r.fixable]
        if not reports:
            summary = f"[#e0af68]No hay archivos .lrc en[/] [dim]{self.state.lyrics_raw}[/]"
        elif not bad:
            summary = f"[#9ece6a]✓ Los {len(reports)} archivos están bien[/]"
        else:
            summary = (
                f"[bold]{len(reports)}[/] archivos · [#9ece6a]{len(reports) - len(bad)} ok[/] · "
                f"[#e0af68]{len(fixable)} reparables[/] · [#f7768e]{len(bad) - len(fixable)} sin sincronía[/]"
            )
            if fixable:
                summary += "  [dim]r = reparar (se guarda un .bak)[/]"
        self.query_one("#check-summary", Static).update(summary)
        self._show_detail(0)

    @on(DataTable.RowHighlighted, "#check-table")
    def _row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key.value is not None:
            self._show_detail(int(event.row_key.value))

    def _show_detail(self, index: int) -> None:
        detail = self.query_one("#check-detail", Static)
        if not 0 <= index < len(self.reports):
            detail.update("")
            return
        report = self.reports[index]
        if report.ok:
            detail.update(f"[dim]{report.path}[/]")
            return
        if not report.fixable:
            detail.update(
                f"[dim]{report.path}[/]\n  [#f7768e]Letra sin marcas de tiempo (texto plano).[/] "
                "No se puede reparar: borrala y volvé a descargarla, o buscala en lrclib.net."
            )
            return
        shown ="\n".join(f"  • {p}" for p in report.problems[:6])
        more = f"\n  … y {len(report.problems) - 6} más" if len(report.problems) > 6 else ""
        detail.update(f"[dim]{report.path}[/]\n{shown}{more}")

    def action_repair(self) -> None:
        self._repair()

    @work(exclusive=True, group="repair")
    async def _repair(self) -> None:
        fixable = [r for r in self.reports if r.fixable]
        if not fixable:
            self.app.notify("No hay archivos reparables", severity="warning", timeout=3)
            return
        if not await self.app.push_screen_wait(
            ConfirmDialog(
                f"¿Reparar {len(fixable)} archivos?\n\n"
                "Se eliminan marcas de tiempo duplicadas, se ordenan las líneas y las líneas "
                "inválidas pasan a comentarios. Se guarda una copia [bold].bak[/] de cada uno."
            )
        ):
            return
        files, issues = repair_reports(fixable)
        self.app.notify(f"✓ {files} archivos reparados ({issues} duplicados eliminados)", timeout=5)
        self._scan()
