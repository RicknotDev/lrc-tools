"""LRC Puller CLI - Batch download synchronized lyrics from LRCLIB."""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

from lrc_tools.audio import get_audio_files
from lrc_tools.config import Config
from lrc_tools.puller import (
    MUTAGEN_AVAILABLE, SYNCEDLYRICS_AVAILABLE,
    extract_metadata, resolve_output_path, save_lyrics, search_song,
)
from rich.traceback import install as install_traceback
install_traceback(show_locals=True)

console = Console()

EPILOG = """
[bold]Examples:[/]
  [dim]# Fetch lyrics for all songs in ~/Music[/]
  lrc-fetch --audio-dir ~/Music --output-dir ~/.local/share/lrc-tools/lyrics/raw

  [dim]# Fetch with custom thread count[/]
  lrc-fetch --audio-dir ~/Music --output-dir ./lyrics --search-threads 8

  [dim]# Overwrite existing .lrc files[/]
  lrc-fetch --audio-dir ~/Music --output-dir ./lyrics --overwrite -y
"""


def main():
    parser = argparse.ArgumentParser(
        description="Batch download LRC lyrics from LRCLIB (with syncedlyrics fallback)",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--audio-dir", type=Path, required=True, help="Directory containing audio files")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory to save .lrc files")
    parser.add_argument("--search-threads", type=int, default=None, help="Concurrent search threads (default: 5)")
    parser.add_argument("--download-threads", type=int, default=None, help="Concurrent download threads (default: 5)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing .lrc files")
    parser.add_argument("--no-preserve-structure", action="store_true", help="Flatten output dir instead of mirroring audio dir structure")
    parser.add_argument("--plain-only", action="store_true", help="Prefer plain lyrics over synced")
    parser.add_argument("--config", type=Path, help="Path to config.yaml")
    parser.add_argument("-y", "--yes", action="store_true", help="Download without confirmation prompt")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded without downloading")

    args = parser.parse_args()

    audio_dir = args.audio_dir
    output_dir = args.output_dir

    if not audio_dir.exists():
        console.print(f"[red]Error:[/] audio directory [bold]{audio_dir}[/] does not exist")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    cfg = Config(args.config).puller if args.config else None

    prefer_synced = not args.plain_only
    preserve_structure = not args.no_preserve_structure
    overwrite = args.overwrite

    def prompt_threads(label, default):
        if default is not None:
            return default
        try:
            default_val = cfg.search_threads if cfg else 5
            return IntPrompt.ask(f"  [bold]{label}[/] threads", default=default_val)
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/]")
            sys.exit(0)

    search_threads = prompt_threads("Search", args.search_threads)
    download_threads = prompt_threads("Download", args.download_threads)

    if cfg and not args.overwrite:
        overwrite = cfg.overwrite
    if cfg and not args.no_preserve_structure:
        preserve_structure = cfg.preserve_structure
    if cfg and not args.plain_only:
        prefer_synced = cfg.prefer_synced

    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold cyan")
    info.add_column()
    info.add_row("Audio dir:", str(audio_dir))
    info.add_row("Output dir:", str(output_dir))
    info.add_row("Threads:", f"{search_threads} search / {download_threads} download")
    info.add_row("Overwrite:", "[green]yes[/]" if overwrite else "[dim]no[/]")
    info.add_row("Struct mirror:", "[green]yes[/]" if preserve_structure else "[dim]no[/]")
    info.add_row("Mutagen:", "[green]yes[/]" if MUTAGEN_AVAILABLE else "[yellow]no[/]")
    info.add_row("Syncedlyrics:", "[green]yes[/]" if SYNCEDLYRICS_AVAILABLE else "[yellow]no[/]")
    console.print(Panel(info, title="[bold]LRC PULLER[/]", border_style="cyan"))

    with console.status("[bold]Scanning for audio files...[/]"):
        audio_files = get_audio_files(audio_dir)

    if not audio_files:
        console.print("[yellow]No audio files found.[/]")
        return 0

    songs = []
    skipped = 0
    for f in audio_files:
        out_path = resolve_output_path(f, audio_dir, output_dir, preserve_structure)
        if out_path.exists() and not overwrite:
            skipped += 1
            continue
        songs.append((f, extract_metadata(f)))

    console.print(f"Found [bold]{len(audio_files)}[/] audio files"
                  f"([dim]{skipped}[/] skipped, [bold]{len(songs)}[/] to fetch)")

    if not songs:
        console.print("[yellow]Nothing to do.[/]")
        return 0

    if songs:
        sample = Table(title="Sample metadata", box=None)
        sample.add_column("#", style="dim")
        sample.add_column("Artist", style="cyan")
        sample.add_column("Title", style="white")
        for i, (fp, meta) in enumerate(songs[:5], 1):
            sample.add_row(str(i), meta.get("artist") or "(no artist)", meta.get("title") or "?")
        if len(songs) > 5:
            sample.add_row("...", f"and {len(songs) - 5} more", "")
        console.print(sample)

    found_results = []
    not_found = 0
    errors = 0

    search_progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )

    with search_progress:
        task = search_progress.add_task("[cyan]Searching lyrics...", total=len(songs))
        with ThreadPoolExecutor(max_workers=search_threads) as executor:
            futures = {executor.submit(search_song, song, prefer_synced): song for song in songs}
            for future in as_completed(futures):
                result = future.result()
                if result["status"] == "found":
                    found_results.append(result)
                elif result["status"] == "error":
                    errors += 1
                    not_found += 1
                else:
                    not_found += 1
                search_progress.update(task, advance=1,
                                       description=f"[cyan]Searching... found {len(found_results)}, errors {errors}")

    console.print(f"\nFound lyrics for [bold]{len(found_results)}/{len(songs)}[/] songs")
    if not_found:
        console.print(f"  [yellow]Not found: {not_found}[/]")

    if not found_results:
        console.print("[yellow]Nothing to download.[/]")
        return 0

    if args.dry_run:
        console.print(f"\n[bold]Dry run:[/] would download [bold]{len(found_results)}[/] files to [bold]{output_dir}[/]")
        for r in found_results:
            filepath, _ = r["song"]
            console.print(f"  {filepath.stem}")
        return 0

    if args.yes:
        confirm = True
    else:
        try:
            confirm = Confirm.ask(f"\nDownload [bold]{len(found_results)}[/] lyrics files?")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/]")
            return 0
        if not confirm:
            console.print("[yellow]Cancelled[/]")
            return 0

    tally = {"success": 0, "error": 0}
    sources = {"lrclib": 0, "syncedlyrics": 0}

    def _save_result(search_result):
        filepath, _ = search_result["song"]
        out_path = resolve_output_path(filepath, audio_dir, output_dir, preserve_structure)
        ok = save_lyrics(search_result["content"], out_path)
        return {"file": filepath.name, "status": "success" if ok else "error", "source": search_result.get("source", "lrclib")}

    save_progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )

    with save_progress:
        stask = save_progress.add_task("[green]Saving lyrics...", total=len(found_results))
        with ThreadPoolExecutor(max_workers=download_threads) as executor:
            futures = {executor.submit(_save_result, r): r for r in found_results}
            for future in as_completed(futures):
                result = future.result()
                status = result["status"]
                tally[status] = tally.get(status, 0) + 1
                if status == "success":
                    sources[result["source"]] = sources.get(result["source"], 0) + 1
                save_progress.update(stask, advance=1)

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold green")
    summary.add_column()
    summary.add_row("Saved:", str(tally["success"]))
    if sources.get("lrclib"):
        summary.add_row("  lrclib:", str(sources["lrclib"]))
    if sources.get("syncedlyrics"):
        summary.add_row("  syncedlyrics:", str(sources["syncedlyrics"]))
    if tally.get("error"):
        summary.add_row("[red]Errors:[/]", str(tally["error"]))
    summary.add_row("Output:", str(output_dir))

    console.print()
    console.print(Panel(summary, title="[bold]Done![/]", border_style="green"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
