from __future__ import annotations

import json
import re
import tomllib
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARITY = ROOT / "parity"
SKILLS = ROOT / "plugins" / "ai-game-studio" / "skills"
AUTOMATION = ROOT / "plugins" / "ai-game-studio-automation" / "templates"
EXPECTED = {
    "skill": 73,
    "role": 49,
    "hook-behavior": 12,
    "rule": 11,
    "template": 40,
    "native-skill": 12,
    "total-core-skills": 85,
}
IMPLICIT_DISABLED = {"setup-engine", "engine-automation", "quality-enhance"}
BANNED_RUNTIME_MARKERS = (
    ".claude/",
    "CLAUDE.md",
    "AskUserQuestion",
    "allowed-tools",
    "WebSearch",
    "model: sonnet",
    "model: opus",
    "model: haiku",
    "maxTurns",
    "disallowedTools",
    "memory: project",
    "Task tool",
    "via Task",
    "Task calls",
    "Write/Edit tools",
)


def frontmatter(path: Path) -> tuple[dict[str, str], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"missing frontmatter: {path}")
    try:
        end = lines[1:].index("---") + 1
    except ValueError as exc:
        raise AssertionError(f"unterminated frontmatter: {path}") from exc
    data: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if not separator:
            raise AssertionError(f"malformed frontmatter line in {path}: {line}")
        value = value.strip()
        data[key] = json.loads(value) if value.startswith('"') else value
    return data, "\n".join(lines[end + 1 :])


def yaml_json_string(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(\".*\")\s*$", text, re.MULTILINE)
    if not match:
        raise AssertionError(f"missing YAML string field: {key}")
    return json.loads(match.group(1))


class ParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads((PARITY / "ledger.json").read_text(encoding="utf-8"))

    def test_exact_ledger_counts(self) -> None:
        self.assertEqual(self.ledger["expected"], EXPECTED)
        self.assertEqual(self.ledger["actual"], EXPECTED)
        counts = Counter(entry["kind"] for entry in self.ledger["entries"])
        self.assertEqual(
            counts,
            Counter({"skill": 73, "role": 49, "hook-behavior": 12, "rule": 11, "template": 40}),
        )
        self.assertEqual(len(self.ledger["entries"]), 185)
        self.assertEqual(len(self.ledger["native_skills"]), 12)

    def test_ledger_provenance_and_uniqueness(self) -> None:
        entries = self.ledger["entries"]
        identities = [(item["kind"], item["id"]) for item in entries]
        self.assertEqual(len(identities), len(set(identities)))
        for entry in entries:
            self.assertRegex(entry["source_commit"], r"^[0-9a-f]{40}$")
            self.assertRegex(entry["source_blob"], r"^[0-9a-f]{40}$")
            self.assertTrue(entry["source_path"])
            self.assertTrue(entry["tests"])
            if entry["kind"] == "hook-behavior":
                self.assertEqual(entry["status"], "replaced")
                self.assertTrue(entry["codex_mappings"])
            else:
                self.assertEqual(entry["status"], "ported")
                self.assertTrue((ROOT / entry["destination"]).is_file())
                for supporting in entry.get("supporting_files", []):
                    self.assertTrue((ROOT / supporting).is_file())

    def test_skill_surface_and_metadata(self) -> None:
        directories = sorted(path for path in SKILLS.iterdir() if path.is_dir())
        self.assertEqual(len(directories), 85)
        ledger_names = {item["id"] for item in self.ledger["entries"] if item["kind"] == "skill"}
        native_names = {item["id"] for item in self.ledger["native_skills"]}
        self.assertEqual({path.name for path in directories}, ledger_names | native_names)

        for directory in directories:
            metadata, _ = frontmatter(directory / "SKILL.md")
            self.assertEqual(set(metadata), {"name", "description"})
            self.assertEqual(metadata["name"], directory.name)
            self.assertTrue(metadata["description"])
            self.assertLessEqual(len((directory / "SKILL.md").read_text(encoding="utf-8").splitlines()), 500)

            product = (directory / "agents" / "openai.yaml").read_text(encoding="utf-8")
            display = yaml_json_string(product, "display_name")
            short = yaml_json_string(product, "short_description")
            prompt = yaml_json_string(product, "default_prompt")
            self.assertTrue(display)
            self.assertGreaterEqual(len(short), 25)
            self.assertLessEqual(len(short), 64)
            self.assertIn(f"$ai-game-studio:{directory.name}", prompt)
            expected = "false" if directory.name in IMPLICIT_DISABLED else "true"
            self.assertRegex(product, rf"(?m)^\s*allow_implicit_invocation:\s*{expected}\s*$")

    def test_namespaced_skill_handoffs(self) -> None:
        names = [path.name for path in SKILLS.iterdir() if path.is_dir()]
        alias = re.compile(
            r"(?<![A-Za-z0-9_./$:-])/(" + "|".join(sorted(map(re.escape, names), key=len, reverse=True)) + r")\b"
        )
        hits = []
        for path in SKILLS.glob("*/SKILL.md"):
            hits.extend((path, match.group(0)) for match in alias.finditer(path.read_text(encoding="utf-8")))
        self.assertEqual(hits, [])

    def test_materialized_template_references_exist(self) -> None:
        pattern = re.compile(r"\.ai-game-studio/templates/([A-Za-z0-9_./-]+\.md)")
        missing = []
        for path in SKILLS.rglob("*.md"):
            for relative in pattern.findall(path.read_text(encoding="utf-8")):
                if not (AUTOMATION / "upstream" / relative).is_file():
                    missing.append((str(path.relative_to(ROOT)), relative))
        self.assertEqual(missing, [])

    def test_agent_rule_and_template_counts(self) -> None:
        agents = sorted((AUTOMATION / "agents").glob("*.toml"))
        rules = sorted((AUTOMATION / "rules").glob("*.md"))
        templates = sorted((AUTOMATION / "upstream").rglob("*.md"))
        self.assertEqual(len(agents), 49)
        self.assertEqual(len(rules), 11)
        self.assertEqual(len(templates), 40)
        for path in agents:
            parsed = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(parsed), {"developer_instructions"})
            self.assertIn("Inherit the active Codex model", parsed["developer_instructions"])

    def test_runtime_has_no_claude_only_declarations(self) -> None:
        roots = [SKILLS, AUTOMATION / "agents", AUTOMATION / "rules", AUTOMATION / "upstream"]
        failures = []
        for root in roots:
            for path in root.rglob("*"):
                if path.is_file() and path.suffix in {".md", ".toml", ".yaml"}:
                    text = path.read_text(encoding="utf-8")
                    for marker in BANNED_RUNTIME_MARKERS:
                        if marker in text:
                            failures.append(f"{path.relative_to(ROOT)}: {marker}")
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
