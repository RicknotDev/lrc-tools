"""Sidebar status panel widget."""

from textual.widgets import Static

from lrc_tools import core


class StatusPanel(Static):
    def refresh_stats(self, state: core.AppState, snapshot: dict | None = None) -> None:
        snapshot = snapshot or core.sidebar_snapshot(state)
        stats = snapshot["stats"]
        missing = snapshot["missing"]
        tools = "\u2713" if stats["tools"] else "\u2717"
        deps_s = "\u2713" if stats["deps_ok"] else "\u2717"
        music = str(stats["music_dir"])
        if len(music) > 22:
            music = "\u2026" + music[-21:]

        lines = [
            "[bold #7aa2f7]Estado[/]", "",
            f"M\u00fasica [dim]{music}[/]",
            f"Canciones  [bold]{stats['audio']}[/]",
            f".lrc       [bold]{stats['lrc']}[/]",
            f".wlrc      [bold]{stats['wlrc']}[/]", "",
            f"Herramientas {tools}",
            f"Deps cr\u00edticas {deps_s}",
        ]
        if missing:
            lines.append(f"[#f7768e]Falta: {', '.join(missing[:2])}[/]")
        lines.extend(["", "[dim]XDG raw[/]", f"[dim]{core.LYRICS_RAW}[/]", "[dim]XDG out[/]", f"[dim]{core.LYRICS_PROCESSED}[/]"])
        self.update("\n".join(lines))
