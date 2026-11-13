"""Keyboard shortcut reference shown with "?"."""

from __future__ import annotations

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from lrc_tools import __version__

SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Menú principal", [
        ("↑ ↓ / Enter", "Moverse y elegir una opción"),
        ("1 – 9, 0", "Ir directo a una opción del menú"),
        ("f", "Descargar letras (fetch)"),
        ("p", "Procesar letras (.lrc → .wlrc)"),
        ("v", "Abrir el visualizador"),
        ("r", "Modo rápido: descargar + procesar"),
        ("c", "Revisar y reparar letras"),
        ("d", "Descargar canciones (spotdl)"),
        ("l", "Mostrar u ocultar el log"),
        ("R", "Actualizar el panel de estado"),
        ("q", "Salir"),
    ]),
    ("Tareas en curso", [
        ("c", "Cancelar la tarea"),
        ("Esc", "Volver (pregunta si hay una tarea corriendo)"),
        ("Ctrl+L", "Limpiar el log"),
    ]),
    ("Elegir canción", [
        ("escribir", "Filtrar por nombre"),
        ("↓ / Enter", "Pasar a la lista / lanzar la primera coincidencia"),
        ("a", "Modo automático (sigue al reproductor)"),
        ("Supr / d", "Borrar la canción seleccionada"),
    ]),
    ("Diálogos", [
        ("y / n", "Sí / No"),
        ("Esc", "Cancelar"),
    ]),
]


def render_help() -> str:
    lines = [f"[bold #7aa2f7]♪ lrc-tools {__version__}[/] [dim]· atajos de teclado[/]", ""]
    for title, rows in SECTIONS:
        lines.append(f"[bold #bb9af7]{title}[/]")
        for key, desc in rows:
            lines.append(f"  [bold #e0af68]{key:<12}[/] {desc}")
        lines.append("")
    lines.append("[dim]Esc, q o ? para cerrar[/]")
    return "\n".join(lines)


class HelpScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    HelpScreen { align: center middle; }
    HelpScreen > VerticalScroll {
        width: 72;
        max-width: 95%;
        height: auto;
        max-height: 90%;
        background: #11182d;
        border: round #7aa2f7;
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Cerrar"),
        Binding("q", "close", show=False),
        Binding("question_mark", "close", show=False),
    ]

    def compose(self):
        with VerticalScroll():
            yield Static(render_help(), id="help-text")

    def action_close(self) -> None:
        self.dismiss(None)
