from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
CORE_DIR = REPO / "plugins" / "ai-game-studio" / "scripts"
sys.path.insert(0, str(CORE_DIR))
import ags_core as core  # noqa: E402
AUTOMATION_SCRIPTS = REPO / "plugins" / "ai-game-studio-automation" / "scripts"
sys.path.insert(0, str(AUTOMATION_SCRIPTS))
import project_setup  # noqa: E402


class PackTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name)
        self.doctor_patch = mock.patch.object(core, "doctor", return_value={"read_only": True, "platform": {"os": "test"}})
        self.doctor_patch.start()

    def tearDown(self) -> None:
        self.doctor_patch.stop()
        self.temporary.cleanup()

    def proposal(self) -> dict:
        with mock.patch.object(core.platform, "system", return_value="Windows"), mock.patch.object(core.platform, "machine", return_value="AMD64"):
            return core.pack_plan("unity", project_root=self.project)

    def test_plan_has_complete_transaction_and_does_not_mutate_project(self) -> None:
        plan = self.proposal()
        for key in ("plan_id", "detected_environment", "exact_actions", "downloads", "licenses", "permissions", "backups", "rollback_operations", "expiry", "digest"):
            self.assertIn(key, plan)
        self.assertEqual(plan["digest"], core.plan_digest(plan))
        self.assertFalse((self.project / core.STATE_DIR).exists())

    def test_apply_requires_digest_and_rejects_tamper_and_replay(self) -> None:
        wrong = self.proposal()
        with self.assertRaises(core.StudioError):
            core.apply_plan(wrong, project_root=self.project, confirmed_digest="0" * 64)
        tampered = copy.deepcopy(wrong)
        tampered["metadata"]["pack_id"] = "changed"
        with self.assertRaises(core.StudioError):
            core.apply_plan(tampered, project_root=self.project, confirmed_digest=wrong["digest"])
        journal = core.apply_plan(wrong, project_root=self.project, confirmed_digest=wrong["digest"])
        self.assertEqual(journal["status"], "applied")
        with self.assertRaises(core.StudioError):
            core.apply_plan(wrong, project_root=self.project, confirmed_digest=wrong["digest"])

    def test_apply_rejects_expired_and_raced_plan(self) -> None:
        expired = self.proposal()
        expired["expiry"] = "2000-01-01T00:00:00Z"
        expired["digest"] = core.plan_digest(expired)
        with self.assertRaises(core.StudioError):
            core.apply_plan(expired, project_root=self.project, confirmed_digest=expired["digest"])
        raced = self.proposal()
        state = self.project / core.STATE_DIR / "project.json"
        state.parent.mkdir(parents=True)
        state.write_text("{}\n", encoding="utf-8")
        with self.assertRaises(core.StudioError):
            core.apply_plan(raced, project_root=self.project, confirmed_digest=raced["digest"])

    def test_apply_then_rollback_restores_original_files(self) -> None:
        state_dir = self.project / core.STATE_DIR
        state_dir.mkdir()
        original_project = '{"schema_version":1,"custom":"keep"}\n'
        original_lock = '{"schema_version":1,"custom_lock":"keep"}\n'
        (state_dir / "project.json").write_text(original_project, encoding="utf-8")
        (state_dir / "lock.json").write_text(original_lock, encoding="utf-8")
        plan = self.proposal()
        transaction = core.apply_plan(plan, project_root=self.project, confirmed_digest=plan["digest"])
        rollback = core.rollback_plan(transaction["transaction_id"], project_root=self.project)
        core.apply_plan(rollback, project_root=self.project, confirmed_digest=rollback["digest"])
        self.assertEqual((state_dir / "project.json").read_text(encoding="utf-8"), original_project)
        self.assertEqual((state_dir / "lock.json").read_text(encoding="utf-8"), original_lock)

    def test_server_executable_is_absolute_and_hash_locked(self) -> None:
        server = self.project / "mock-server.exe"
        server.write_bytes(b"mock server")
        digest = core.file_sha256(server)
        with mock.patch.object(core.platform, "system", return_value="Windows"), mock.patch.object(core.platform, "machine", return_value="AMD64"):
            with self.assertRaises(core.StudioError):
                core.pack_plan("unity", project_root=self.project, executable=str(server), executable_sha256="0" * 64)
            plan = core.pack_plan("unity", project_root=self.project, executable=str(server), executable_sha256=digest, server_args=("--stdio",))
        core.apply_plan(plan, project_root=self.project, confirmed_digest=plan["digest"])
        state = json.loads((self.project / core.STATE_DIR / "project.json").read_text(encoding="utf-8"))
        configured = state["active_packs"]["unity"]["server"]
        self.assertTrue(configured["enabled"])
        self.assertEqual(configured["sha256"], digest)
        self.assertEqual(configured["args"], ["--stdio"])
        self.assertTrue(core.pack_doctor(self.project)["healthy"])

    def test_documented_alternative_provider_is_selectable_and_pinned(self) -> None:
        with mock.patch.object(core.platform, "system", return_value="Windows"), mock.patch.object(core.platform, "machine", return_value="AMD64"):
            plan = core.pack_plan("unity", project_root=self.project, provider="IvanMurzak/Unity-MCP")
        self.assertEqual(plan["metadata"]["provider"], "IvanMurzak/Unity-MCP")
        self.assertEqual(plan["licenses"][0]["spdx"], "Apache-2.0")
        self.assertIn("f6db1c27e7f0d647dd3a127e2fff3a65c5785cc5", plan["downloads"][0]["url"])

    def test_mcp_adapter_health_check_never_launches_server(self) -> None:
        server = self.project / "mock-server.exe"
        server.write_bytes(b"mock server that must not be launched")
        with mock.patch.object(core.platform, "system", return_value="Windows"), mock.patch.object(core.platform, "machine", return_value="AMD64"):
            plan = core.pack_plan("unity", project_root=self.project, executable=str(server), executable_sha256=core.file_sha256(server))
        core.apply_plan(plan, project_root=self.project, confirmed_digest=plan["digest"])
        adapter = REPO / "plugins" / "ai-game-studio-unity" / "scripts" / "mcp_adapter.py"
        result = subprocess.run([sys.executable, str(adapter), "--pack", "unity", "--doctor"], cwd=self.project, capture_output=True, text=True, check=False, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["healthy"])
        server.write_bytes(b"tampered")
        rejected = subprocess.run([sys.executable, str(adapter), "--pack", "unity", "--doctor"], cwd=self.project, capture_output=True, text=True, check=False, timeout=10)
        self.assertEqual(rejected.returncode, 78)
        self.assertIn("hash", rejected.stderr.lower())

    def test_path_escape_is_rejected_while_planning(self) -> None:
        with self.assertRaises(core.StudioError):
            core.make_plan(kind="test", project_root=self.project, actions=[core.write_action("../escape.json", {})])

    def test_non_uuid_plan_and_transaction_ids_are_rejected(self) -> None:
        plan = self.proposal()
        plan["plan_id"] = "../../outside"
        plan["digest"] = core.plan_digest(plan)
        with self.assertRaises(core.StudioError):
            core.apply_plan(plan, project_root=self.project, confirmed_digest=plan["digest"])
        with self.assertRaises(core.StudioError):
            core.rollback_plan("../../outside", project_root=self.project)

    def test_project_setup_selects_common_and_only_requested_engine_roles(self) -> None:
        plan = project_setup.build_plan(core, self.project, "unity")
        targets = {action["target"] for action in plan["exact_actions"]}
        self.assertIn("AGENTS.md", targets)
        self.assertIn("Assets/Scripts/AGENTS.md", targets)
        self.assertIn(".codex/agents/producer.toml", targets)
        self.assertIn(".codex/agents/unity-specialist.toml", targets)
        self.assertNotIn(".codex/agents/godot-specialist.toml", targets)
        self.assertFalse((self.project / "AGENTS.md").exists())

    def test_claude_migration_is_planned_reversible_and_codex_native(self) -> None:
        source = "# Claude Code\nUse /brainstorm and .claude/skills.\nmodel: claude-sonnet\ntools: Bash, Read\n"
        (self.project / "CLAUDE.md").write_text(source, encoding="utf-8")
        (self.project / ".claude" / "hooks").mkdir(parents=True)
        (self.project / ".claude" / "hooks" / "guard.sh").write_text("exit 0\n", encoding="utf-8")
        plan = core.migrate_claude_plan(self.project)
        self.assertFalse((self.project / "AGENTS.md").exists())
        self.assertIn(".claude/hooks/guard.sh", plan["metadata"]["review_required"])
        core.apply_plan(plan, project_root=self.project, confirmed_digest=plan["digest"])
        migrated = (self.project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("$ai-game-studio:brainstorm", migrated)
        self.assertIn(".codex/skills", migrated)
        self.assertNotIn("Claude", migrated)
        self.assertNotIn("model:", migrated.lower())
        self.assertEqual((self.project / "CLAUDE.md").read_text(encoding="utf-8"), source)


if __name__ == "__main__":
    unittest.main()
