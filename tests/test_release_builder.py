from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools import build_release


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseBuilderTests(unittest.TestCase):
    def test_release_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-release-a-") as first, tempfile.TemporaryDirectory(
            prefix="ags-release-b-"
        ) as second:
            first_dir, second_dir = Path(first), Path(second)
            build_release.build(ROOT, first_dir, "1.0.0")
            build_release.build(ROOT, second_dir, "1.0.0")
            first_files = sorted(path.name for path in first_dir.iterdir())
            second_files = sorted(path.name for path in second_dir.iterdir())
            self.assertEqual(first_files, second_files)
            self.assertEqual(11, len(first_files))
            for name in first_files:
                self.assertEqual(digest(first_dir / name), digest(second_dir / name), name)

            manifest = json.loads((first_dir / "release-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("1.0.0", manifest["version"])
            self.assertEqual(9, len(manifest["artifacts"]))
            sbom = json.loads((first_dir / "codex-ai-game-studio-v1.0.0.spdx.json").read_text(encoding="utf-8"))
            self.assertEqual("SPDX-2.3", sbom["spdxVersion"])
            self.assertGreater(len(sbom["files"]), 100)

    def test_archives_use_safe_sorted_paths_and_fixed_timestamps(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-release-zip-") as temporary:
            output = Path(temporary)
            build_release.build(ROOT, output, "1.0.0")
            for archive_path in output.glob("*.zip"):
                with zipfile.ZipFile(archive_path) as archive:
                    names = archive.namelist()
                    self.assertEqual(sorted(names), names, archive_path.name)
                    self.assertTrue(names)
                    for info in archive.infolist():
                        self.assertEqual(build_release.FIXED_ZIP_TIME, info.date_time)
                        self.assertFalse(info.filename.startswith("/"))
                        self.assertNotIn("..", Path(info.filename).parts)

    def test_release_excludes_ignored_temp_and_custom_output_trees(self) -> None:
        ignored_root = ROOT / ".tmp"
        ignored_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="release-input-", dir=ignored_root) as ignored, tempfile.TemporaryDirectory(
            prefix="release-output-", dir=ROOT
        ) as output:
            ignored_sentinel = Path(ignored) / "must-not-ship.txt"
            output_sentinel = Path(output) / "must-not-recurse.txt"
            ignored_sentinel.write_text("ignored", encoding="utf-8")
            output_sentinel.write_text("old output", encoding="utf-8")
            selected = build_release.release_files(ROOT, output=Path(output).resolve())
            self.assertNotIn(ignored_sentinel, selected)
            self.assertNotIn(output_sentinel, selected)
            build_release.build(ROOT, Path(output), "1.0.0")
            with zipfile.ZipFile(Path(output) / "codex-ai-game-studio-v1.0.0.zip") as archive:
                names = archive.namelist()
                self.assertFalse(any("must-not-ship.txt" in name for name in names))
                self.assertFalse(any("must-not-recurse.txt" in name for name in names))


if __name__ == "__main__":
    unittest.main()
