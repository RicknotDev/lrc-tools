"""Quick mode screen — fetch then process, without a confirmation prompt."""

from __future__ import annotations

from lrc_tools import core
from lrc_tools.tui.screens.task import TaskScreen


class QuickScreen(TaskScreen):
    def __init__(self, state: core.AppState) -> None:
        super().__init__("quick", state, ask_confirm=False)
