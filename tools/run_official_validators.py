#!/usr/bin/env python3
"""Discover and run the official Codex plugin and skill validators.

CI supplies a pinned checkout of openai/codex. Local runs discover the validators
bundled with Codex Desktop or accept explicit paths. No validator is vendored in
this repository.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


def candidates(explicit: Path | None, relative: str) -> list[Path]:
    result: list[Path] = []
    if explicit:
        result.append(explicit)
    official_root = os.environ.get("CODEX_OFFICIAL_SKILLS_ROOT")
    if official_root:
        result.append(Path(official_root) / relative)
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    result.extend(
        (
            codex_home / "skills" / ".system" / relative,
            codex_home / "vendor_imports" / "skills" / "skills" / ".system" / relative,
        )
    )
    deduplicated: list[Path] = []
    for item in result:
        resolved = item.expanduser().resolve()
        if resolved not in deduplicated:
            deduplicated.append(resolved)
    return deduplicated


def first_file(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.is_file()), None)


def run(command: list[str]) -> bool:
    print("+", " ".join(command))
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
    )
    if result.returncode:
        if result.stdout:
            print(result.stdout.rstrip())
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
    else:
        message = result.stdout.strip().splitlines()
        print(message[-1] if message else "Official validator passed.")
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--plugin-validator", type=Path)
    parser.add_argument("--skill-validator", type=Path)
    parser.add_argument("--require", action="store_true", help="fail if either official validator is unavailable")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    plugin_validator = first_file(
        candidates(args.plugin_validator, "plugin-creator/scripts/validate_plugin.py")
    )
    skill_validator = first_file(
        candidates(args.skill_validator, "skill-creator/scripts/quick_validate.py")
    )
    missing = []
    if not plugin_validator:
        missing.append("plugin-creator validate_plugin.py")
    if not skill_validator:
        missing.append("skill-creator quick_validate.py")
    if missing:
        print("Official validators unavailable: " + ", ".join(missing))
        if args.require:
            return 2

    ok = True
    if plugin_validator:
        for plugin_dir in sorted((root / "plugins").iterdir()):
            if plugin_dir.is_dir():
                ok = run([sys.executable, str(plugin_validator), str(plugin_dir)]) and ok
    if skill_validator:
        for skill_file in sorted((root / "plugins").glob("*/skills/*/SKILL.md")):
            ok = run([sys.executable, str(skill_validator), str(skill_file.parent)]) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
