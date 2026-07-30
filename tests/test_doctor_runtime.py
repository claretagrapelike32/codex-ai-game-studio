from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
CORE_DIR = REPO / "plugins" / "ai-game-studio" / "scripts"
sys.path.insert(0, str(CORE_DIR))
import ags_core as core  # noqa: E402


class DoctorTests(unittest.TestCase):
    def test_detects_representative_projects_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            unity = root / "unity" / "ProjectSettings"
            unity.mkdir(parents=True)
            (unity / "ProjectVersion.txt").write_text("m_EditorVersion: 6000.1.2f1\n", encoding="utf-8")
            godot = root / "godot"
            godot.mkdir()
            (godot / "project.godot").write_text("[application]\n", encoding="utf-8")
            unreal = root / "unreal"
            unreal.mkdir()
            (unreal / "Demo.uproject").write_text('{"EngineAssociation":"5.6"}\n', encoding="utf-8")
            before = sorted(str(path.relative_to(root)) for path in root.rglob("*"))
            findings = core.detect_projects(root)
            after = sorted(str(path.relative_to(root)) for path in root.rglob("*"))
            self.assertEqual(before, after)
            self.assertEqual({item["engine"] for item in findings}, {"unity", "godot", "unreal"})
            self.assertEqual(next(item for item in findings if item["engine"] == "unity")["version"], "6000.1.2f1")

    def test_doctor_never_returns_credential_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict("os.environ", {"OPENAI_API_KEY": "super-secret-value"}, clear=False), mock.patch.object(core, "detect_apps", return_value={}), mock.patch.object(core, "detect_gpu", return_value={}), mock.patch.object(core, "run_probe", return_value={"available": False}):
            report = core.doctor(Path(temporary))
            self.assertEqual(report["credentials"]["available_variable_names"], ["OPENAI_API_KEY"])
            self.assertFalse(report["credentials"]["values_read"])
            self.assertNotIn("super-secret-value", str(report))
            self.assertTrue(report["read_only"])
            self.assertFalse(report["network"]["performed"])

    def test_mcp_detection_only_reports_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".mcp.json").write_text('{"mcpServers":{"unity":{"env":{"TOKEN":"secret"}}}}', encoding="utf-8")
            result = core.detect_mcp(root)
            self.assertEqual(result["server_names"], ["unity"])
            self.assertNotIn("secret", str(result))


if __name__ == "__main__":
    unittest.main()
