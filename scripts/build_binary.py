#!/usr/bin/env python3
"""Build standalone binary for lrc-tools using PyInstaller."""

import os
import subprocess
import sys


def main():
    dist_dir = os.path.join(os.path.dirname(__file__), "..", "dist")
    work_dir = os.path.join(os.path.dirname(__file__), "..", "build", "pyinstaller")

    entry_points = {
        "lrc-tools": "lrc_tools.cli.tui:main",
        "lrc-fetch": "lrc_tools.cli.fetch:main",
        "lrc-processor": "lrc_tools.cli.process:main",
        "lrc-vis": "lrc_tools.cli.vis:main",
    }

    base_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--distpath", dist_dir,
        "--workpath", work_dir,
        "--clean",
        "--noconfirm",
        "--onefile",
    ]

    for name, entry in entry_points.items():
        print(f"Building {name}...")
        cmd = base_cmd + [
            "--name", name,
            "--hidden-import", "yaml",
            "--collect-all", "lrc_tools",
            "--add-data", "src/lrc_tools:tests" if os.name == "nt" else "src/lrc_tools:tests",
        ]
        if sys.platform == "win32":
            cmd.append("--console")
        cmd.extend(["--specpath", work_dir])
        cmd.append(f"-c{entry}")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  FAILED: {result.stderr}")
            return 1
        print(f"  OK: {os.path.join(dist_dir, name)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
