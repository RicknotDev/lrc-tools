#!/usr/bin/env python3
"""Build standalone one-file binaries for lrc-tools using PyInstaller.

PyInstaller needs a real script as its entry point, so a tiny launcher is
generated for every console script and then frozen into ``dist/<name>[.exe]``.

Usage:
    python scripts/build_binary.py            # build every binary
    python scripts/build_binary.py lrc-tools  # build only the named ones
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
WORK_DIR = ROOT / "build" / "pyinstaller"

ENTRY_POINTS = {
    "lrc-tools": "lrc_tools.cli.tui",
    "lrc-fetch": "lrc_tools.cli.fetch",
    "lrc-processor": "lrc_tools.cli.process",
    "lrc-vis": "lrc_tools.cli.vis",
}

LAUNCHER = """import sys
from {module} import main

sys.exit(main())
"""

# Packages that load parts of themselves dynamically and are missed by
# PyInstaller's static analysis unless collected explicitly.
COLLECT = ["lrc_tools", "rich", "textual", "syncedlyrics", "mutagen"]


def _installed(module: str) -> bool:
    try:
        __import__(module)
    except ImportError:
        return False
    return True


def build(name: str, module: str) -> bool:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    launcher = WORK_DIR / f"{name.replace('-', '_')}_launcher.py"
    launcher.write_text(LAUNCHER.format(module=module), encoding="utf-8")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--console", "--clean", "--noconfirm",
        "--name", name,
        "--distpath", str(DIST_DIR),
        "--workpath", str(WORK_DIR / name),
        "--specpath", str(WORK_DIR),
        "--hidden-import", "yaml",
    ]
    for pkg in COLLECT:
        if _installed(pkg):
            cmd += ["--collect-all", pkg]
    cmd.append(str(launcher))

    print(f"Building {name}...", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(result.stdout[-4000:])
        print(result.stderr[-4000:], file=sys.stderr)
        print(f"  FAILED: {name}", file=sys.stderr)
        return False

    exe = DIST_DIR / (name + (".exe" if sys.platform == "win32" else ""))
    print(f"  OK: {exe}")
    return True


def main(argv: list[str]) -> int:
    names = argv or list(ENTRY_POINTS)
    unknown = [n for n in names if n not in ENTRY_POINTS]
    if unknown:
        print(f"Unknown binary: {', '.join(unknown)} (choose from {', '.join(ENTRY_POINTS)})")
        return 2
    ok = all([build(n, ENTRY_POINTS[n]) for n in names])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
