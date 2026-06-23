"""Display utilities for LRC visualizer."""

import os
import sys
from typing import Optional


def _supports_ansi() -> bool:
    """Check if terminal supports ANSI escape sequences."""
    if os.name == "nt":
        # Windows 10+ ConPTY / Windows Terminal / PowerShell ISE support ANSI
        # Only old CMD without Virtual Terminal Processing does not.
        return bool(os.environ.get("WT_SESSION")  # Windows Terminal
                    or os.environ.get("TERM_PROGRAM")  # VS Code, etc.
                    or "ANSICON" in os.environ
                    or os.environ.get("ConEmuANSI") == "ON")
    return True


def get_terminal_size() -> tuple:
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except Exception:
        return 80, 24


def clear_screen():
    if _supports_ansi():
        sys.stdout.write("\033[2J\033[H")
    else:
        os.system("cls" if os.name == "nt" else "clear")
    sys.stdout.flush()


def hide_cursor():
    if _supports_ansi():
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()


def show_cursor():
    if _supports_ansi():
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


FALLBACK_CHARS = {
    'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A', 'Æ': 'A',
    'Ç': 'C', 'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
    'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
    'Ð': 'D', 'Ñ': 'N', 'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O', 'Ø': 'O',
    'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U', 'Ý': 'Y', 'Þ': 'P', 'ß': 'B', 'Œ': 'O',
}


def render_block_text(text: str, font_data: dict) -> str:
    text = text.upper()
    height = len(font_data.get("A", [""]))
    lines = ["" for _ in range(height)]

    for char in text:
        mapped = FALLBACK_CHARS.get(char, char)
        if mapped in font_data:
            char_lines = font_data[mapped]
            for i in range(height):
                if i < len(char_lines):
                    lines[i] += char_lines[i] + " "
                else:
                    lines[i] += " " * (len(char_lines[0]) + 1)
        else:
            space_width = len(font_data.get(" ", ["    "])[0])
            for i in range(height):
                lines[i] += " " * (space_width + 1)

    cols, rows = get_terminal_size()
    max_width = max(len(line) for line in lines) if lines else 0
    if max_width > cols:
        lines = [line[:cols] for line in lines]

    pad_top = max(0, (rows - len(lines)) // 2)

    output = []
    for i in range(rows):
        if pad_top <= i < pad_top + len(lines):
            line = lines[i - pad_top]
            pad_left = max(0, (cols - len(line)) // 2)
            centered = " " * pad_left + line
            output.append(centered.ljust(cols))
        else:
            output.append(" " * cols)

    return "\n".join(output)


def render_simple_text(text: str, centered: bool = True) -> str:
    cols, rows = get_terminal_size()
    if centered:
        pad_top = rows // 2
        pad_left = max(0, (cols - len(text)) // 2)
        output = []
        for i in range(rows):
            if i == pad_top:
                output.append(" " * pad_left + text)
            else:
                output.append(" " * cols)
        return "\n".join(output)
    return text


def render_waiting() -> str:
    return render_simple_text("\u2022\u2022\u2022", centered=True)


def display_text(
    text: str,
    use_block_letters: bool = True,
    font_data: Optional[dict] = None,
    clear: bool = True,
):
    if clear:
        clear_screen()
    if use_block_letters and font_data:
        output = render_block_text(text, font_data)
    else:
        output = render_simple_text(text)
    sys.stdout.write(output)
    sys.stdout.flush()


def display_waiting(clear: bool = True):
    if clear:
        clear_screen()
    output = render_waiting()
    sys.stdout.write(output)
    sys.stdout.flush()
