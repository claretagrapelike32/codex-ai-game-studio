#!/usr/bin/env python3
"""Plan/apply reversible project guidance and selected Codex role materialization."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


COMMON_ROLES = (
    "producer",
    "game-designer",
    "gameplay-programmer",
    "qa-lead",
    "technical-artist",
    "art-director",
    "audio-director",
    "devops-engineer",
    "performance-analyst",
    "accessibility-specialist",
    "security-engineer",
)
ENGINE_ROLES = {
    "unity": (
        "unity-specialist",
        "unity-addressables-specialist",
        "unity-dots-specialist",
        "unity-shader-specialist",
        "unity-ui-specialist",
    ),
    "godot": (
        "godot-specialist",
        "godot-csharp-specialist",
        "godot-gdextension-specialist",
        "godot-gdscript-specialist",
        "godot-shader-specialist",
    ),
    "unreal": (
        "unreal-specialist",
        "ue-blueprint-specialist",
        "ue-gas-specialist",
        "ue-replication-specialist",
        "ue-umg-specialist",
    ),
    "browser": (),
    "generic": (),
}
SCOPES = {
    "unity": (("Assets/AGENTS.md", "AGENTS.assets.md"), ("Assets/Scripts/AGENTS.md", "AGENTS.code.md")),
    "godot": (("assets/AGENTS.md", "AGENTS.assets.md"), ("scripts/AGENTS.md", "AGENTS.code.md")),
    "unreal": (("Content/AGENTS.md", "AGENTS.assets.md"), ("Source/AGENTS.md", "AGENTS.code.md")),
    "browser": (("public/AGENTS.md", "AGENTS.assets.md"), ("src/AGENTS.md", "AGENTS.code.md")),
    "generic": (("assets/AGENTS.md", "AGENTS.assets.md"), ("src/AGENTS.md", "AGENTS.code.md")),
}


def load_core(explicit: str | None) -> ModuleType:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("AI_GAME_STUDIO_CORE_SCRIPT"):
        candidates.append(Path(os.environ["AI_GAME_STUDIO_CORE_SCRIPT"]))
    plugin_root = Path(__file__).resolve().parents[1]
    candidates.append(plugin_root.parent / "ai-game-studio" / "scripts" / "ags_core.py")
    for candidate in candidates:
        if not candidate.is_file():
            continue
        spec = importlib.util.spec_from_file_location("ai_game_studio_core", candidate)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise RuntimeError("Cannot find ags_core.py. Install the core plugin or pass --core-script.")


def build_plan(core: ModuleType, project: Path, engine: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    template_root = root / "templates" / "project"
    actions: list[dict[str, Any]] = []
    for target, source in (("AGENTS.md", "AGENTS.root.md"), *SCOPES[engine]):
        content = (template_root / source).read_text(encoding="utf-8")
        actions.append({
            "operation": "write-file",
            "target": target,
            "content_base64": __import__("base64").b64encode(content.encode("utf-8")).decode("ascii"),
        })
    roles = [*COMMON_ROLES, *ENGINE_ROLES[engine]]
    agent_root = root / "templates" / "agents"
    missing: list[str] = []
    for role in roles:
        source = agent_root / f"{role}.toml"
        if not source.is_file():
            missing.append(role)
            continue
        actions.append({
            "operation": "write-file",
            "target": f".codex/agents/{role}.toml",
            "content_base64": __import__("base64").b64encode(source.read_bytes()).decode("ascii"),
        })
    state, lock = core.state_documents(project)
    state["automation"] = {
        "engine": engine,
        "selected_roles": [role for role in roles if role not in missing],
        "missing_role_templates": missing,
        "hooks_require_trust_via": "/hooks",
    }
    actions.extend([
        core.write_action(f"{core.STATE_DIR}/project.json", state),
        core.write_action(f"{core.STATE_DIR}/lock.json", lock),
    ])
    return core.make_plan(
        kind="automation-project-setup",
        project_root=project,
        actions=actions,
        permissions=["write project guidance", "materialize selected local Codex agent profiles"],
        metadata={"engine": engine, "selected_roles": roles, "missing_role_templates": missing},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-script")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--project", default=".")
    plan.add_argument("--engine", choices=sorted(ENGINE_ROLES), required=True)
    plan.add_argument("--output")
    apply = sub.add_parser("apply")
    apply.add_argument("--project", default=".")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--confirmed-digest", required=True)
    args = parser.parse_args()
    try:
        core = load_core(args.core_script)
        if args.command == "plan":
            proposal = build_plan(core, Path(args.project), args.engine)
            if args.output:
                core.atomic_write(Path(args.output).resolve(), core.json_bytes(proposal))
            print(json.dumps(proposal, indent=2, sort_keys=True))
        else:
            proposal = core.safe_json_load(Path(args.plan).resolve())
            result = core.apply_plan(proposal, project_root=Path(args.project), confirmed_digest=args.confirmed_digest)
            print(json.dumps(result, indent=2, sort_keys=True))
    except (OSError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
