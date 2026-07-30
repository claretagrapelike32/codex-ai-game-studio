#!/usr/bin/env python3
"""Exercise confirmed pack apply, disable, and rollback against a temp project."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


PACKS = ("unity", "godot", "unreal", "blender", "pixel")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def invoke(cli: Path, *arguments: str) -> dict[str, object]:
    command = [sys.executable, str(cli), *arguments]
    result = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(arguments)}\n{result.stderr}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"command emitted malformed JSON: {' '.join(arguments)}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("command output must be a JSON object")
    return value


def plan_and_apply(cli: Path, project: Path, pack: str) -> dict[str, object]:
    plan_path = project / f"{pack}-enable-plan.json"
    executable = Path(sys.executable).resolve()
    invoke(
        cli,
        "pack",
        "plan",
        pack,
        "--project",
        str(project),
        "--server-executable",
        str(executable),
        "--server-sha256",
        digest(executable),
        "--server-arg",
        "ai-game-studio-mock",
        "--output",
        str(plan_path),
    )
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    return invoke(
        cli,
        "pack",
        "apply",
        "--project",
        str(project),
        "--plan",
        str(plan_path),
        "--confirmed-digest",
        str(plan["digest"]),
    )


def apply_plan(cli: Path, project: Path, plan_path: Path) -> dict[str, object]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    return invoke(
        cli,
        "pack",
        "apply",
        "--project",
        str(project),
        "--plan",
        str(plan_path),
        "--confirmed-digest",
        str(plan["digest"]),
    )


def exercise(cli: Path, pack: str) -> None:
    with tempfile.TemporaryDirectory(prefix=f"ai-game-studio-{pack}-") as temporary:
        project = Path(temporary).resolve()
        applied = plan_and_apply(cli, project, pack)
        transaction_id = str(applied["transaction_id"])
        state = json.loads((project / ".ai-game-studio" / "project.json").read_text(encoding="utf-8"))
        if pack not in state.get("active_packs", {}):
            raise RuntimeError(f"{pack} was not activated")
        health = invoke(cli, "pack", "doctor", "--project", str(project))
        if not health.get("healthy"):
            raise RuntimeError(f"{pack} mock health check failed: {health}")

        rollback_path = project / f"{pack}-rollback-plan.json"
        invoke(cli, "pack", "rollback", transaction_id, "--project", str(project), "--output", str(rollback_path))
        apply_plan(cli, project, rollback_path)
        state_path = project / ".ai-game-studio" / "project.json"
        state_after = json.loads(state_path.read_text(encoding="utf-8")) if state_path.is_file() else {}
        if pack in state_after.get("active_packs", {}):
            raise RuntimeError(f"{pack} rollback left the pack active")

        plan_and_apply(cli, project, pack)
        disable_path = project / f"{pack}-disable-plan.json"
        invoke(cli, "pack", "disable", pack, "--project", str(project), "--output", str(disable_path))
        apply_plan(cli, project, disable_path)
        disabled = json.loads((project / ".ai-game-studio" / "project.json").read_text(encoding="utf-8"))
        if pack in disabled.get("active_packs", {}):
            raise RuntimeError(f"{pack} disable left the pack active")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", choices=PACKS, required=True)
    parser.add_argument("--cli", type=Path, default=root / "plugins" / "ai-game-studio" / "scripts" / "ai_game_studio.py")
    args = parser.parse_args()
    exercise(args.cli.resolve(), args.pack)
    print(json.dumps({"pack": args.pack, "status": "passed"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
