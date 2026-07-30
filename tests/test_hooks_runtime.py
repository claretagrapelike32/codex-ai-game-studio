from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins" / "ai-game-studio-automation"
DISPATCH = PLUGIN / "scripts" / "hook_dispatch.py"
FIXTURES = REPO / "tests" / "fixtures" / "runtime" / "hooks"
EXPECTED_EVENTS = {"SessionStart", "SubagentStart", "SubagentStop", "PreCompact", "PostCompact", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"}


class HookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.data = Path(self.temporary.name) / "plugin-data"
        self.project.mkdir()
        (self.project / "assets").mkdir()
        (self.project / "assets" / "generated.png").write_bytes(b"not a png")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def fixture(self, name: str) -> dict:
        payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        payload["cwd"] = str(self.project)
        return payload

    def dispatch(self, payload: dict) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PLUGIN_ROOT"] = str(PLUGIN)
        env["PLUGIN_DATA"] = str(self.data)
        return subprocess.run([sys.executable, str(DISPATCH)], input=json.dumps(payload), capture_output=True, text=True, env=env, cwd=self.project, check=False, timeout=10)

    def test_hook_config_uses_official_plugin_shape_and_cross_platform_commands(self) -> None:
        config = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(set(config["hooks"]), EXPECTED_EVENTS)
        for groups in config["hooks"].values():
            for group in groups:
                for handler in group["hooks"]:
                    self.assertEqual(handler["type"], "command")
                    self.assertIn("${PLUGIN_ROOT}", handler["command"])
                    self.assertIn("%PLUGIN_ROOT%", handler["commandWindows"])
        session_end = config["hooks"]["SessionEnd"][0]["hooks"][0]
        self.assertLessEqual(session_end["timeout"], 3)

    def test_all_configured_events_have_realistic_fixtures(self) -> None:
        files = {path.stem for path in FIXTURES.glob("*.json")}
        expected_files = {"session_start", "subagent_start", "subagent_stop", "pre_compact", "post_compact", "pre_tool_use", "post_tool_use", "stop", "session_end"}
        self.assertEqual(files, expected_files)
        for name in sorted(expected_files):
            result = self.dispatch(self.fixture(name + ".json"))
            self.assertEqual(result.returncode, 0, f"{name}: {result.stderr}")
            if result.stdout.strip():
                json.loads(result.stdout)

    def test_force_push_is_denied(self) -> None:
        result = self.dispatch(self.fixture("pre_tool_use.json"))
        payload = json.loads(result.stdout)
        decision = payload["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("force", decision["permissionDecisionReason"].lower())

    def test_commit_with_malformed_transaction_state_is_denied(self) -> None:
        state = self.project / ".ai-game-studio"
        state.mkdir()
        (state / "project.json").write_text("not-json", encoding="utf-8")
        payload = self.fixture("pre_tool_use.json")
        payload["tool_input"]["command"] = "git commit -m safe-looking"
        result = self.dispatch(payload)
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("invalid json", decision["permissionDecisionReason"].lower())

    def test_bare_push_from_main_is_denied(self) -> None:
        git = self.project / ".git"
        git.mkdir()
        (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
        payload = self.fixture("pre_tool_use.json")
        payload["tool_input"]["command"] = "git push origin"
        result = self.dispatch(payload)
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("main", decision["permissionDecisionReason"].lower())

    def test_invalid_changed_asset_returns_post_tool_feedback(self) -> None:
        result = self.dispatch(self.fixture("post_tool_use.json"))
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("PNG", payload["reason"])

    def test_audit_log_excludes_transcript_and_message_contents(self) -> None:
        self.dispatch(self.fixture("subagent_stop.json"))
        self.dispatch(self.fixture("stop.json"))
        log_text = (self.data / "audit" / "events.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("Private content", log_text)
        self.assertNotIn("transcript.jsonl", log_text)
        self.assertNotIn("agent.jsonl", log_text)
        self.assertIn("log-agent-stop", log_text)
        self.assertIn("session-stop", log_text)

    def test_all_twelve_mapped_behaviors_are_declared(self) -> None:
        namespace: dict = {"__name__": "hook_fixture"}
        exec(DISPATCH.read_text(encoding="utf-8"), namespace)
        self.assertEqual(len(namespace["BEHAVIORS"]), 12)
        self.assertEqual(len(set(namespace["BEHAVIORS"])), 12)


if __name__ == "__main__":
    unittest.main()
