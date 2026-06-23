"""Tests for core.py (stdlib only, no network)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lrc_tools import core


class TestAppState(unittest.TestCase):
    def test_roundtrip(self) -> None:
        state = core.AppState(music_dir=Path("/tmp/music"))
        data = state.to_dict()
        restored = core.AppState.from_dict(data)
        self.assertEqual(restored.music_dir, Path("/tmp/music"))
        self.assertEqual(restored.lyrics_raw, core.LYRICS_RAW)

    def test_from_dict_defaults(self) -> None:
        s = core.AppState.from_dict({})
        self.assertTrue(str(s.music_dir).endswith("Music") or "music" in str(s.music_dir).lower())


class TestPaths(unittest.TestCase):
    def test_normalize_tilde(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = core.normalize_path(tmp)
            self.assertTrue(p.is_absolute())
            self.assertEqual(p, Path(tmp).resolve())

    def test_validate_music_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ok, _ = core.validate_music_dir(Path(tmp))
            self.assertTrue(ok)
        ok, msg = core.validate_music_dir(Path("/no/existe/lrc-tools-test"))
        self.assertFalse(ok)
        self.assertIn("existe", msg)

    def test_list_subdirs_skips_hidden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "visible").mkdir()
            (root / ".hidden").mkdir()
            names = [p.name for p in core.list_subdirs(root)]
            self.assertIn("visible", names)
            self.assertNotIn(".hidden", names)


class TestCounts(unittest.TestCase):
    def test_count_audio_recursive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a").mkdir()
            (root / "a" / "song.mp3").write_bytes(b"x")
            (root / "note.txt").write_text("x")
            self.assertEqual(core.count_audio(root), 1)

    def test_count_files_glob(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sub").mkdir()
            (root / "sub" / "x.lrc").write_text("[00:00.00] hi")
            (root / "y.wlrc").write_text("w")
            self.assertEqual(core.count_files(root, "*.lrc"), 1)
            self.assertEqual(core.count_files(root, "*.wlrc"), 1)


class TestConfig(unittest.TestCase):
    def test_config_yaml_preserve_structure(self) -> None:
        text = core.config_yaml()
        self.assertIn("preserve_structure: true", text)
        self.assertIn("search_threads: 4", text)

    def test_config_summary_missing_file(self) -> None:
        with mock.patch.object(core, "CONFIG_FILE", Path("/nonexistent/config.yaml")):
            s = core.config_summary()
            self.assertIn("preserve_structure", s)


class TestCommands(unittest.TestCase):
    def test_fetch_cmd_flags(self) -> None:
        state = core.AppState(music_dir=Path("/music"))
        with mock.patch.object(core, "lrc_tool_cmd", return_value="/usr/bin/lrc-fetch"):
            cmd = core.fetch_cmd(state)
        self.assertIn("--audio-dir", cmd)
        self.assertIn("music", cmd[cmd.index("--audio-dir") + 1])
        self.assertIn(str(core.LYRICS_RAW), cmd)
        self.assertIn("--search-threads", cmd)
        self.assertIn("-y", cmd)

    def test_process_cmd_wlrc(self) -> None:
        state = core.AppState(music_dir=Path("/music"))
        with mock.patch.object(core, "lrc_tool_cmd", return_value="/usr/bin/lrc-processor"):
            cmd = core.process_cmd(state)
        self.assertIn("--wlrc", cmd)
        self.assertIn(str(core.LYRICS_PROCESSED), cmd)

    def test_vis_cmd_short(self) -> None:
        state = core.AppState(music_dir=Path("/music"))
        with mock.patch.object(core, "lrc_tool_cmd", return_value="/usr/bin/lrc-vis"):
            cmd = core.vis_cmd(state)
        self.assertEqual(cmd[0], "/usr/bin/lrc-vis")
        self.assertIn("--lrc-dir", cmd)
        self.assertIn("--wlrc", cmd)

    def test_vis_cmd_pinned_file(self) -> None:
        state = core.AppState(music_dir=Path("/music"))
        lrc = Path("/tmp/song.wlrc")
        with mock.patch.object(core, "lrc_tool_cmd", return_value="/usr/bin/lrc-vis"):
            cmd = core.vis_cmd(state, lrc_file=lrc)
        self.assertIn("--lrc-file", cmd)
        self.assertIn("--pin", cmd)
        self.assertIn("--play", cmd)
        self.assertIn("--audio-dir", cmd)
        self.assertIn("music", cmd[cmd.index("--audio-dir") + 1])

    def test_list_tracks_recursive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root / "Artist"
            sub.mkdir()
            (sub / "a.wlrc").write_text("x")
            (root / "b.wlrc").write_text("y")
            tracks = core.list_tracks(root)
            self.assertEqual(len(tracks), 2)
            labels = {t.label for t in tracks}
            self.assertIn("b.wlrc", labels)
            self.assertTrue(any("Artist" in lb for lb in labels))


class TestStateFile(unittest.TestCase):
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "lrc-tools"
            cfg.mkdir()
            state_path = cfg / ".setup_done"
            with mock.patch.object(core, "CONFIG_DIR", cfg), mock.patch.object(core, "STATE_FILE", state_path):
                state = core.AppState(music_dir=Path("/my/music"))
                core.save_state(state)
                loaded = core.load_state()
                self.assertIsNotNone(loaded)
                assert loaded is not None
                self.assertEqual(loaded.music_dir, Path("/my/music"))

    def test_load_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".setup_done"
            path.write_text("{not json", encoding="utf-8")
            with mock.patch.object(core, "STATE_FILE", path):
                self.assertIsNone(core.load_state())


class TestDependencies(unittest.TestCase):
    def test_scan_returns_textual(self) -> None:
        keys = {d.key for d in core.scan_dependencies()}
        self.assertIn("textual", keys)
        self.assertIn("playerctl", keys)

    def test_critical_excludes_textual_by_default(self) -> None:
        with mock.patch.object(core, "scan_dependencies") as scan:
            scan.return_value = [
                core.Dependency("t", "textual", False, True, "", None),
                core.Dependency("p", "playerctl", True, True, "", None),
            ]
            self.assertTrue(core.critical_deps_ok())
            self.assertFalse(core.critical_deps_ok(include_tui=True))


class TestRepoRoot(unittest.TestCase):
    def test_repo_root_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "setup.sh").write_text("#!/bin/bash\n")
            os.environ["LRC_TOOLS_REPO"] = str(root)
            self.assertEqual(core.repo_root(), root.resolve())
            del os.environ["LRC_TOOLS_REPO"]


if __name__ == "__main__":
    unittest.main()
