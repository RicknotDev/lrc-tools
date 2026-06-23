"""Local audio playback for visualizer (mpv IPC, ffplay fallback)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

IS_WIN = os.name == "nt"


class LocalAudioPlayer:
    def __init__(self) -> None:
        self._proc: Optional[subprocess.Popen] = None
        self._ipc_path: Optional[str] = None
        self._backend: Optional[str] = None
        self._start_mono: float = 0.0

    def play(self, path: Path) -> bool:
        self.stop()
        path = path.resolve()
        if not path.is_file():
            return False
        if self._try_mpv(path):
            return True
        return self._try_ffplay(path)

    def _try_mpv(self, path: Path) -> bool:
        if not shutil.which("mpv"):
            return False
        # Windows: skip mpv IPC — use ffplay fallback instead (no position feedback needed)
        if IS_WIN:
            return False
        self._ipc_path = os.path.join(
            tempfile.gettempdir(), f"lrc-tools-{os.getpid()}.sock"
        )
        try:
            os.unlink(self._ipc_path)
        except OSError:
            pass
        try:
            self._proc = subprocess.Popen(
                [
                    "mpv", "--no-video", "--really-quiet", "--keep-open=no",
                    f"--input-ipc-server={self._ipc_path}", str(path),
                ],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError:
            return False
        for _ in range(60):
            if os.path.exists(self._ipc_path):
                self._backend = "mpv"
                return True
            if self._proc.poll() is not None:
                self.stop()
                return False
            time.sleep(0.05)
        self.stop()
        return False

    def _mpv_command(self, command: list[Any]) -> Optional[dict]:
        if not self._ipc_path:
            return None
        try:
            import socket
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.4)
                sock.connect(self._ipc_path)
                sock.sendall((json.dumps({"command": command}) + "\n").encode())
                buf = b""
                while b"\n" not in buf:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                if buf:
                    return json.loads(buf.decode().split("\n", 1)[0])
        except (OSError, json.JSONDecodeError, ValueError):
            pass
        return None

    def _try_ffplay(self, path: Path) -> bool:
        if not shutil.which("ffplay"):
            return False
        try:
            self._proc = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError:
            return False
        self._start_mono = time.monotonic()
        self._backend = "ffplay"
        return True

    def get_position(self) -> Optional[float]:
        if self._proc and self._proc.poll() is not None:
            return None
        if self._backend == "mpv":
            resp = self._mpv_command(["get_property", "time-pos"])
            if resp and resp.get("error") == "success" and resp.get("data") is not None:
                return float(resp["data"])
        elif self._backend == "ffplay":
            return time.monotonic() - self._start_mono
        return None

    def get_status(self) -> Optional[str]:
        if self._proc and self._proc.poll() is not None:
            return "Stopped"
        if self._backend == "mpv":
            resp = self._mpv_command(["get_property", "pause"])
            if resp and resp.get("error") == "success":
                return "Paused" if resp.get("data") else "Playing"
        if self._proc and self._proc.poll() is None:
            return "Playing"
        return "Stopped"

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):
                try:
                    self._proc.kill()
                except OSError:
                    pass
        self._proc = None
        if self._ipc_path:
            try:
                os.unlink(self._ipc_path)
            except OSError:
                pass
        self._ipc_path = None
        self._backend = None


def resolve_audio_for_lyrics(lrc_path: Path, audio_dir: Optional[Path]) -> Optional[Path]:
    if not audio_dir or not audio_dir.is_dir():
        return None
    from lrc_tools.audio import find_audio_for_lrc
    return find_audio_for_lrc(lrc_path, audio_dir)
