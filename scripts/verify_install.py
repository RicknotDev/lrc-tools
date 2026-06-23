#!/usr/bin/env python3
"""Post-install verification for lrc-tools."""

import shutil
import sys
from pathlib import Path


def main():
    errors = 0

    print("lrc-tools verification")
    print("=" * 40)

    # 1. Check package import
    try:
        from lrc_tools import __version__
        print(f"  Package: lrc-tools v{__version__}")
    except ImportError:
        print("  Package: FAILED (cannot import lrc_tools)")
        errors += 1

    # 2. Check CLI entry points
    for cmd in ["lrc-tools", "lrc-fetch", "lrc-processor", "lrc-vis"]:
        path = shutil.which(cmd)
        if path:
            print(f"  {cmd}: {path}")
        else:
            print(f"  {cmd}: NOT FOUND")
            errors += 1

    # 3. Check Python version
    pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info >= (3, 12):
        print(f"  Python: {pyver} OK")
    else:
        print(f"  Python: {pyver} (need 3.12+)")
        errors += 1

    # 4. Check critical deps
    try:
        from lrc_tools import core
        deps = core.scan_dependencies()
        critical_ok = core.critical_deps_ok()
        missing = [d for d in deps if d.critical and not d.present and not (d.key == "playerctl" and not core.IS_LINUX)]
        if missing:
            print(f"  Missing critical: {[d.label for d in missing]}")
            errors += 1
        else:
            print("  Critical deps: OK")
    except Exception as e:
        print(f"  Dep check FAILED: {e}")
        errors += 1

    print("=" * 40)
    if errors:
        print(f"FAILED: {errors} issue(s) found")
        return 1
    print("PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
