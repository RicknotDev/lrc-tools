"""LRC Visualizer CLI - Display synchronized lyrics."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from lrc_tools.fonts import get_font, load_fonts_from_json, register_font
from lrc_tools.visualizer import run_visualizer
from rich.traceback import install as install_traceback
install_traceback(show_locals=True)

console = Console()

EPILOG = """
[bold]Examples:[/]
  [dim]# Auto-match lyrics from media player (playerctl)[/]
  lrc-vis --lrc-dir ~/.local/share/lrc-tools/lyrics/processed --wlrc

  [dim]# Play a specific song with local audio[/]
  lrc-vis --lrc-dir ./processed --wlrc --lrc-file ./processed/song.wlrc \\
          --audio-dir ~/Music --play

  [dim]# Custom display font[/]
  lrc-vis --lrc-dir ./processed --wlrc --font compact --refresh-rate 0.1
"""


def main():
    parser = argparse.ArgumentParser(
        description="LRC Lyrics Visualizer — displays synced lyrics in the terminal",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--lrc-dir", type=Path, required=True, help="Directory containing LRC files")
    parser.add_argument("--audio-dir", type=Path, help="Directory containing audio files")
    parser.add_argument("--wlrc", action="store_true", help="LRC files are word-level (WLRC format)")
    parser.add_argument("--font", type=str, default="block", help="Font to use (default: block)")
    parser.add_argument("--custom-fonts", type=Path, help="Path to custom fonts JSON file")
    parser.add_argument("--refresh-rate", type=float, default=None, help="Display refresh rate in seconds (default: 0.05)")
    parser.add_argument("--config", type=Path, help="Path to config.yaml")
    parser.add_argument("--lrc-file", type=Path, help="Use this lyric file instead of auto-matching from player")
    parser.add_argument("--pin", action="store_true", help="Keep showing --lrc-file even if the player changes track")
    parser.add_argument("--play", action="store_true", help="Play matching audio locally (mpv/ffplay) while visualizing")
    parser.add_argument("--no-play", action="store_true", help="Do not start local playback even with --lrc-file")

    args = parser.parse_args()

    if not args.lrc_dir.exists():
        console.print(f"[red]Error:[/] LRC directory [bold]{args.lrc_dir}[/] does not exist")
        return 1

    if args.custom_fonts and not args.custom_fonts.exists():
        console.print(f"[red]Error:[/] custom fonts file [bold]{args.custom_fonts}[/] does not exist")
        return 1

    if args.lrc_file and not args.lrc_file.is_file():
        console.print(f"[red]Error:[/] lrc file [bold]{args.lrc_file}[/] does not exist")
        return 1

    if not args.lrc_file and not args.audio_dir:
        console.print("[dim]No --lrc-file provided: will auto-match from media player (playerctl)[/]")

    if args.play and not args.audio_dir and not args.lrc_file:
        console.print("[yellow]Warning:[/] --play requires --lrc-file and --audio-dir to work")

    if args.custom_fonts:
        custom = load_fonts_from_json(args.custom_fonts)
        for name, data in custom.items():
            if not name.startswith("_"):
                register_font(name, data)

    font_data = get_font(args.font)
    pin = args.pin or (args.lrc_file is not None)
    play_audio = args.play or (args.lrc_file is not None and not args.no_play)

    if play_audio and not args.audio_dir:
        play_audio = False

    console.print()
    console.print(Panel(
        f"[bold]LRC directory:[/] {args.lrc_dir}\n"
        f"[bold]Font:[/] {args.font}\n"
        f"[bold]Audio dir:[/] {args.audio_dir or '[dim](none)[/]'}\n"
        f"[bold]Track:[/] {args.lrc_file.name if args.lrc_file else '[dim]auto (playerctl)[/]'}\n"
        f"[bold]Play audio:[/] {'[green]yes[/]' if play_audio else '[dim]no[/]'}\n"
        f"[dim]Press Ctrl+C to exit[/]",
        title="[bold]LRC VISUALIZER[/]",
        border_style="cyan",
    ))

    try:
        return run_visualizer(
            lrc_dir=args.lrc_dir, audio_dir=args.audio_dir, is_wlrc=args.wlrc,
            font_data=font_data, refresh_rate=args.refresh_rate or 0.05,
            fixed_lrc=args.lrc_file, pin_track=pin, play_audio=play_audio,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/]")
        return 0


if __name__ == "__main__":
    sys.exit(main())
