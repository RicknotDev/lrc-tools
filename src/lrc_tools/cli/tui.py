"""Entry point for lrc-tools TUI."""

from __future__ import annotations

import importlib
import subprocess
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.traceback import install as install_traceback

install_traceback(show_locals=False)

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
            console.print('Install it with: [bold]python -m pip install textual[/]')
            return 1
        # Run through the current interpreter so this works even when the
        # console scripts are not on PATH (common with `pip install --user` on Windows).
        modules = {2: "lrc_tools.cli.fetch", 3: "lrc_tools.cli.process", 4: "lrc_tools.cli.vis"}
        if choice in modules:
            return subprocess.call([sys.executable, "-m", modules[choice], "--help"])
        if choice == 5:
            console.print("[green]Goodbye![/]")
            return 0
        console.print("[red]Invalid option.[/]")


def main() -> int:
    if any(arg in ("--version", "-V") for arg in sys.argv[1:]):
        from lrc_tools import __version__

        print(f"lrc-tools {__version__}")
        return 0
    try:
        importlib.import_module("textual")
    except ImportError:
        return _simple_menu()

    from lrc_tools.tui.app import main as tui_main

    return tui_main() or 0


if __name__ == "__main__":
    sys.exit(main())
