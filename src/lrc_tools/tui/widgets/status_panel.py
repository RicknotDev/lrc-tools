"""Sidebar status panel widget."""

from __future__ import annotations

from pathlib import Path

from textual.widgets import Static

from lrc_tools import core

OK = "[#9ece6a]✓[/]"
BAD = "[#f7768e]✗[/]"


def _shorten(path: str, width: int = 24) -> str:
    return path if len(path) <= width else "…" + path[-(width - 1):]


def next_step(stats: dict) -> str:
    """Suggest what the user should do next, based on the current library state."""
    lrc, wlrc = int(stats["lrc"]), int(stats["wlrc"])
    # Lyrics already on disk come first: the visualizer can follow the media player
    # even when the music folder is empty or missing.
    if lrc > wlrc:
        return f"Procesá {lrc - wlrc} letras pendientes [bold](p)[/]"
    if wlrc:
        return "¡Todo listo! Abrí el visualizador [bold](v)[/]"
    if not Path(str(stats["music_dir"])).is_dir():
        return "Elegí tu carpeta de música [bold](7)[/]"
    if not stats["audio"]:
        return "No hay canciones: descargá [bold](6)[/] o cambiá la carpeta [bold](7)[/]"
    return "Descargá las letras [bold](f)[/]"


class StatusPanel(Static):
    def refresh_stats(self, state: core.AppState, snapshot: dict | None = None) -> None:
        snapshot = snapshot or core.sidebar_snapshot(state)
        stats = snapshot["stats"]
        missing = snapshot["missing"]

        lines = [
            "[bold #7aa2f7]Estado[/]",
            "",
            "[dim]Música[/]",
            _shorten(str(stats["music_dir"])),
            "",
            f"Canciones  [bold]{stats['audio']:>6}[/]",
            f".lrc       [bold]{stats['lrc']:>6}[/]",
            f".wlrc      [bold]{stats['wlrc']:>6}[/]",
            "",
            f"{OK if stats['tools'] else BAD} Herramientas",
            f"{OK if stats['deps_ok'] else BAD} Dependencias",
        ]
        if missing:
            lines.append(f"[#f7768e]  Falta: {', '.join(missing[:2])}[/]")
        lines += ["", "[bold #bb9af7]Siguiente paso[/]", next_step(stats)]
        self.update("\n".join(lines))
