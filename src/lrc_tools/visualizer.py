"""LRC Visualizer - Main display loop with player synchronization."""

import threading
import time
from pathlib import Path
from typing import Optional


class SyncData:
    def __init__(self):
        self._lock = threading.Lock()
        self.position: Optional[float] = None
        self.should_resync: bool = False
        self.running: bool = True
        self.current_title: Optional[str] = None
        self.paused: bool = False
        self.pinned_lrc: Optional[Path] = None
        self.pinned_title: Optional[str] = None


def position_monitor(sync_data: SyncData, get_position_func, get_track_func, get_status_func):
    last_check = time.time()
    expected_pos = None

    while sync_data.running:
        time.sleep(0.2)

        track_info = get_track_func()
        with sync_data._lock:
            if track_info and sync_data.current_title and not sync_data.pinned_lrc:
                if track_info[1] != sync_data.current_title:
                    sync_data.should_resync = True
                    continue

            if sync_data.position is None:
                continue

        actual_pos = get_position_func()
        if actual_pos is None:
            continue

        status = get_status_func()
        if status == "Paused":
            with sync_data._lock:
                sync_data.position = actual_pos
                sync_data.should_resync = True
                sync_data.paused = True
            expected_pos = None
            continue

        with sync_data._lock:
            sync_data.paused = False

        if expected_pos is None:
            expected_pos = actual_pos
        else:
            elapsed = time.time() - last_check
            expected_pos += elapsed

        if abs(actual_pos - expected_pos) > 1.0:
            with sync_data._lock:
                sync_data.position = actual_pos
                sync_data.should_resync = True

        expected_pos = actual_pos
        last_check = time.time()


def run_visualizer(
    lrc_dir: Path,
    audio_dir: Optional[Path] = None,
    is_wlrc: bool = False,
    font_data: Optional[dict] = None,
    refresh_rate: float = 0.05,
    fixed_lrc: Optional[Path] = None,
    pin_track: bool = False,
    play_audio: bool = False,
) -> int:
    import sys

    from lrc_tools.audio import find_lrc_for_audio
    from lrc_tools.parser import parse_lrc_simple
    from lrc_tools.display import clear_screen, display_text, display_waiting, hide_cursor, show_cursor
    from lrc_tools.player import get_audio_file_info, get_position, get_status, get_track

    hide_cursor()
    clear_screen()
    display_waiting()

    sync_data = SyncData()
    local_player = None
    get_pos = get_position
    get_trk = get_track
    get_st = get_status

    if fixed_lrc and pin_track:
        sync_data.pinned_lrc = fixed_lrc.resolve()
        sync_data.pinned_title = fixed_lrc.stem

    if play_audio and fixed_lrc and audio_dir:
        from lrc_tools.audio_player import LocalAudioPlayer, resolve_audio_for_lyrics

        audio_path = resolve_audio_for_lyrics(fixed_lrc, audio_dir)
        if audio_path:
            local_player = LocalAudioPlayer()
            if local_player.play(audio_path):
                pinned_title = sync_data.pinned_title or fixed_lrc.stem

                def pinned_track_func() -> tuple[str, str]:
                    return ("", pinned_title)

                get_pos = local_player.get_position
                get_st = local_player.get_status
                get_trk = pinned_track_func
                print(f"Playing: {audio_path.name}", file=sys.stderr)
            else:
                print("Could not play (install mpv or ffplay).", file=sys.stderr)
                local_player = None
        else:
            print(f"No audio found for {fixed_lrc.name} in {audio_dir}", file=sys.stderr)

    monitor_thread = threading.Thread(
        target=position_monitor,
        args=(sync_data, get_pos, get_trk, get_st),
        daemon=True,
    )
    monitor_thread.start()

    try:
        last_title = None

        while sync_data.running:
            if local_player and get_st() == "Stopped":
                return 10

            if sync_data.pinned_lrc:
                lrc = sync_data.pinned_lrc
                title = sync_data.pinned_title or lrc.stem
                artist = ""
                if local_player:
                    song_changed = False
                    last_title = title
                else:
                    track = get_trk()
                    if not track:
                        time.sleep(0.5)
                        continue
                    song_changed = last_title and title != last_title
                    last_title = title
            else:
                track = get_trk()
                if not track:
                    time.sleep(1)
                    continue

                artist, title = track
                song_changed = last_title and title != last_title
                last_title = title

                audio_file = get_audio_file_info()
                lrc = find_lrc_for_audio(
                    audio_file if audio_file else Path(title),
                    lrc_dir, artist, title, is_wlrc=is_wlrc,
                )

                if not lrc:
                    time.sleep(1)
                    continue

            sync_data.current_title = title
            lines = parse_lrc_simple(lrc)
            if not lines:
                time.sleep(1)
                continue

            pos = get_pos()
            if pos is None:
                if local_player and get_st() == "Stopped":
                    return 10
                time.sleep(1)
                continue

            if song_changed and pos > 5.0:
                for _ in range(20):
                    pos = get_pos()
                    if pos is not None and pos < 5.0:
                        break
                    time.sleep(0.1)
                pos = get_pos()
                if pos is None:
                    time.sleep(1)
                    continue

            idx = 0
            for i, (start, _) in enumerate(lines):
                if pos < start:
                    break
                idx = i

            start_time = time.time()
            start_pos = pos
            with sync_data._lock:
                sync_data.position = pos

            while idx < len(lines):
                if local_player and get_st() == "Stopped":
                    return 10

                with sync_data._lock:
                    if sync_data.should_resync:
                        if not sync_data.pinned_lrc:
                            new_track = get_trk()
                            if not new_track or new_track[1] != title:
                                break

                        new_pos = sync_data.position
                        start_time = time.time()
                        start_pos = new_pos

                        idx = 0
                        for i, (start, _) in enumerate(lines):
                            if new_pos >= start:
                                idx = i
                            else:
                                break

                        sync_data.should_resync = False

                elapsed = time.time() - start_time
                current_pos = start_pos + elapsed

                _, text = lines[idx]
                display_text(text, use_block_letters=True, font_data=font_data, clear=True)

                if idx + 1 < len(lines):
                    next_start, _ = lines[idx + 1]
                    if current_pos >= next_start:
                        idx += 1
                        continue

                time.sleep(refresh_rate)

    except KeyboardInterrupt:
        return 0
    finally:
        sync_data.running = False
        if local_player:
            local_player.stop()
        show_cursor()
        clear_screen()

    return 0
