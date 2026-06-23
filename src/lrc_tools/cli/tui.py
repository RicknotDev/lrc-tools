"""Entry point for lrc-tools TUI."""

from __future__ import annotations

import importlib
import subprocess
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.traceback import install as install_traceback

install_traceback(show_locals=True)

console = Console()


def _simple_menu() -> int:
    console.print(Panel("[bold]lrc-tools[/]\n[dim]Terminal synced lyrics toolkit[/]", border_style="cyan"))

    while True:
        console.print("[bold]1[/]) Launch interactive TUI")
        console.print("[bold]2[/]) Run [cyan]lrc-fetch[/]")
        console.print("[bold]3[/]) Run [cyan]lrc-processor[/]")
        console.print("[bold]4[/]) Run [cyan]lrc-vis[/]")
        console.print("[bold]5[/]) Exit")

        try:
            choice = IntPrompt.ask("Select an option", choices=["1", "2", "3", "4", "5"])
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/]")
            return 0

        if choice == 1:
            console.print("[yellow]Textual is not installed.[/]")
            console.print('Install it with: [bold]python3 -m pip install --user "lrc-tools[tui]"[/]')
            return 1
        if choice == 2:
            return subprocess.call(["lrc-fetch", "--help"])
        if choice == 3:
            return subprocess.call(["lrc-processor", "--help"])
        if choice == 4:
            return subprocess.call(["lrc-vis", "--help"])
        if choice == 5:
            console.print("[green]Goodbye![/]")
            return 0
        console.print("[red]Invalid option.[/]")


def main() -> int:
    try:
        importlib.import_module("textual")
    except ImportError:
        return _simple_menu()

    from lrc_tools.tui.app import main as tui_main

    return tui_main() or 0


if __name__ == "__main__":
    sys.exit(main())
