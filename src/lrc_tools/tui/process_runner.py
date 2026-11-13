"""Run a CLI subprocess from the TUI, stream its output and allow cancelling it."""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Callable

# Exit code reported when the user cancelled the process.
CANCELLED = -999


class ProcessRunner:
    """Streams a child process line by line into a callback.

    * stdin is closed so a child can never block the TUI waiting for input.
    * ``COLUMNS`` is set so rich-based CLIs wrap to the log width, not 80 columns.
    """

    def __init__(self, columns: int = 120) -> None:
        self.columns = columns
        self.proc: asyncio.subprocess.Process | None = None
        self.cancelled = False
        self.started_at: float | None = None

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.returncode is None

    @property
    def elapsed(self) -> float:
        return 0.0 if self.started_at is None else time.monotonic() - self.started_at

    async def run(self, cmd: list[str], write: Callable[[str], None]) -> int:
        env = {
            **os.environ,
            "COLUMNS": str(max(40, self.columns)),
            "PYTHONUNBUFFERED": "1",
            "PYTHONIOENCODING": "utf-8",
        }
        self.cancelled = False
        self.started_at = time.monotonic()
        self.proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )
        assert self.proc.stdout
        while line := await self.proc.stdout.readline():
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                write(text)
        code = await self.proc.wait()
        return CANCELLED if self.cancelled else code

    def cancel(self) -> bool:
        """Terminate the running process. Returns False if nothing was running."""
        if not self.running:
            return False
        self.cancelled = True
        assert self.proc
        try:
            self.proc.terminate()
        except ProcessLookupError:
            pass
        return True


def format_elapsed(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}:{secs:02d}"
