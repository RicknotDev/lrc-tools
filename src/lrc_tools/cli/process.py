"""LRC Processor CLI - Split and convert LRC files to word-level timing."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.panel import Panel
from rich.table import Table

from lrc_tools.config import Config
from lrc_tools.processor import process_lrc_file
from rich.traceback import install as install_traceback
install_traceback(show_locals=True)

console = Console()

EPILOG = """
[bold]Examples:[/]
  [dim]# Convert .lrc to word-level .wlrc[/]
  lrc-processor --lrc-dir ~/.local/share/lrc-tools/lyrics/raw \\
                --audio-dir ~/Music \\
                --output-dir ~/.local/share/lrc-tools/lyrics/processed \\
                --wlrc

  [dim]# Process without audio (estimated durations)[/]
  lrc-processor --lrc-dir ./raw --output-dir ./out --no-require-audio

  [dim]# Custom split settings[/]
  lrc-processor --lrc-dir ./raw --audio-dir ./music --output-dir ./out \\
                --wlrc --max-phrase-duration 3.0 --max-words 10
"""


def main():
    parser = argparse.ArgumentParser(
        description="Process LRC files: split long phrases and optionally convert to word-level WLRC",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--lrc-dir", type=Path, required=True, help="Directory containing input .lrc files")
    parser.add_argument("--audio-dir", type=Path, help="Directory containing audio files")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory to write processed files")
    parser.add_argument("--wlrc", action="store_true", help="Convert output to word-level WLRC format")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    parser.add_argument("--no-require-audio", action="store_true", help="Process files even if no matching audio is found")
    parser.add_argument("--max-phrase-duration", type=float, default=None, help="Max phrase duration in seconds (default: 2.5)")
    parser.add_argument("--min-phrase-duration", type=float, default=None, help="Min phrase duration in seconds, shorter are skipped (default: 0.3)")
    parser.add_argument("--max-words", type=int, default=None, help="Max words per phrase (default: 8)")
    parser.add_argument("--no-split-commas", action="store_true", help="Do not split phrases at commas")
    parser.add_argument("--onset-detection", action="store_true", help="Use librosa onset detection for word timing")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-file output")
    parser.add_argument("--config", type=Path, help="Path to config.yaml")

    args = parser.parse_args()

    lrc_dir = args.lrc_dir
    output_dir = args.output_dir

    if not lrc_dir.exists():
        console.print(f"[red]Error:[/] LRC directory [bold]{lrc_dir}[/] does not exist")
        return 1

    if args.audio_dir and not args.audio_dir.exists():
        console.print(f"[red]Error:[/] audio directory [bold]{args.audio_dir}[/] does not exist")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    cfg = Config(args.config).processor if args.config else None

    max_phrase_duration = args.max_phrase_duration or (cfg.max_phrase_duration if cfg else 2.5)
    min_phrase_duration = args.min_phrase_duration or (cfg.min_phrase_duration if cfg else 0.3)
    max_words_per_phrase = args.max_words or (cfg.max_words_per_phrase if cfg else 8)
    split_on_commas = not args.no_split_commas
    use_onset_detection = args.onset_detection or (cfg.use_onset_detection if cfg else False)
    onset_blend_factor = cfg.onset_blend_factor if cfg else 0.5
    require_audio = not args.no_require_audio
    verbose = not args.quiet

    lrc_files = list(lrc_dir.rglob("*.lrc"))

    if not lrc_files:
        console.print(f"[yellow]No .lrc files found in[/] [bold]{lrc_dir}[/]")
        return 0

    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold cyan")
    info.add_column()
    info.add_row("Input dir:", str(lrc_dir))
    info.add_row("Output dir:", str(output_dir))
    info.add_row("Audio dir:", str(args.audio_dir) if args.audio_dir else "[dim](none)[/]")
    info.add_row("Output format:", "[bold]WLRC (word-level)[/]" if args.wlrc else "LRC (phrase-level)")
    info.add_row("Max duration:", f"{max_phrase_duration}s")
    info.add_row("Max words:", str(max_words_per_phrase))
    info.add_row("Split commas:", "[green]yes[/]" if split_on_commas else "[dim]no[/]")
    info.add_row("Onset detect:", "[green]yes[/]" if use_onset_detection else "[dim]no[/]")
    info.add_row("Require audio:", "[green]yes[/]" if require_audio else "[dim]no[/]")
    info.add_row("Overwrite:", "[green]yes[/]" if args.overwrite else "[dim]no[/]")
    info.add_row("Files found:", str(len(lrc_files)))
    console.print(Panel(info, title="[bold]LRC PROCESSOR[/]", border_style="cyan"))

    success = 0
    skipped = 0

    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("[dim]{task.completed}/{task.total}[/]"),
        console=console,
    )

    with progress:
        task = progress.add_task("[cyan]Processing...", total=len(lrc_files))
        for lrc_path in lrc_files:
            result = process_lrc_file(
                lrc_path=lrc_path, audio_dir=args.audio_dir, output_dir=output_dir,
                max_phrase_duration=max_phrase_duration,
                min_phrase_duration=min_phrase_duration,
                max_words_per_phrase=max_words_per_phrase,
                split_on_commas=split_on_commas,
                require_audio=require_audio, overwrite=args.overwrite,
                output_wlrc=args.wlrc, use_onset_detection=use_onset_detection,
                onset_blend_factor=onset_blend_factor, verbose=verbose,
            )
            if result is True:
                success += 1
            elif result is False:
                skipped += 1
            progress.update(task, advance=1, description=f"[cyan]Processing... {success} ok, {skipped} skipped")

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("[green]Processed:[/]", str(success))
    summary.add_row("[dim]Skipped:[/]", str(skipped))
    summary.add_row("Output:", str(output_dir))

    console.print()
    console.print(Panel(summary, title="[bold]Done![/]", border_style="green"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
