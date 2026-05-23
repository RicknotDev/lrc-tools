"""
LRC Visualizer CLI - Display synchronized lyrics
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='LRC Lyrics Visualizer with Playerctl integration'
    )
    parser.add_argument('--lrc-dir', type=Path, required=True,
                        help='Directory containing LRC files')
    parser.add_argument('--audio-dir', type=Path,
                        help='Directory containing audio files')
    parser.add_argument('--wlrc', action='store_true',
                        help='LRC files are word-level (WLRC format)')
    parser.add_argument('--font', type=str, default='block',
                        help='Font to use (default: block)')
    parser.add_argument('--custom-fonts', type=Path,
                        help='Path to custom fonts JSON file')
    parser.add_argument('--refresh-rate', type=float, default=0.05,
                        help='Display refresh rate in seconds (default: 0.05)')
    parser.add_argument('--config', type=Path,
                        help='Path to config.yaml')
    parser.add_argument('--lrc-file', type=Path,
                        help='Use this lyric file instead of auto-matching from player')
    parser.add_argument('--pin', action='store_true',
                        help='Keep showing --lrc-file even if the player changes track')
    parser.add_argument('--play', action='store_true',
                        help='Play matching audio locally (mpv/ffplay) while visualizing')
    parser.add_argument('--no-play', action='store_true',
                        help='Do not start local playback even with --lrc-file')

    args = parser.parse_args()

    lrc_dir = args.lrc_dir
    if not lrc_dir.exists():
        print(f"Error: LRC directory {lrc_dir} does not exist", file=sys.stderr)
        return 1

    try:
        from .fonts import get_font, load_fonts_from_json, register_font
        from .visualizer_main import run_visualizer
    except ImportError as e:
        print(f"Error: could not import visualizer modules — {e}")
        return 1

    # Load custom fonts if provided
    if args.custom_fonts:
        if not args.custom_fonts.exists():
            print(f"Error: custom fonts file {args.custom_fonts} does not exist", file=sys.stderr)
            return 1
        custom = load_fonts_from_json(args.custom_fonts)
        for name, data in custom.items():
            if not name.startswith('_'):  # skip comment keys
                register_font(name, data)

    font_data = get_font(args.font)

    fixed_lrc = args.lrc_file
    if fixed_lrc and not fixed_lrc.is_file():
        print(f"Error: lrc file {fixed_lrc} does not exist", file=sys.stderr)
        return 1

    pin = args.pin or (fixed_lrc is not None)
    play_audio = args.play or (fixed_lrc is not None and not args.no_play)

    print(f"Starting LRC visualizer...")
    print(f"LRC directory: {lrc_dir}")
    if fixed_lrc:
        print(f"Pinned track: {fixed_lrc.name}")
    if play_audio and args.audio_dir:
        print(f"Audio library: {args.audio_dir}")
    elif play_audio and not args.audio_dir:
        print("Aviso: --play requiere --audio-dir para encontrar el archivo", file=sys.stderr)
        play_audio = False
    print(f"Font: {args.font}")
    print(f"Press Ctrl+C to exit")
    print()

    try:
        run_visualizer(
            lrc_dir=lrc_dir,
            audio_dir=args.audio_dir,
            is_wlrc=args.wlrc,
            font_data=font_data,
            refresh_rate=args.refresh_rate,
            fixed_lrc=fixed_lrc,
            pin_track=pin,
            play_audio=play_audio,
        )
    except KeyboardInterrupt:
        print("\nExiting...")
        return 0


if __name__ == '__main__':
    sys.exit(main())
