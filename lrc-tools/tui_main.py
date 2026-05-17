"""Entry point for lrc-tools TUI (installed as lrc_tools.tui_main)."""
try:
    from lrc_tools.tui.app import main
except ImportError:
    from tui.app import main

if __name__ == "__main__":
    main()
