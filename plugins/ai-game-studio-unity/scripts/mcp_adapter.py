#!/usr/bin/env python3
"""Safe stdio adapter gate for an externally installed editor MCP server."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


MAX_CONFIG_BYTES = 1024 * 1024


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_state(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        state = candidate / ".ai-game-studio" / "project.json"
        if state.is_file():
            return state
    return None


def load_selection(pack_id: str) -> tuple[dict[str, Any], Path]:
    state_path = find_state(Path.cwd())
    if state_path is None:
        raise RuntimeError("No .ai-game-studio/project.json found; run pack plan and apply after confirmation")
    if state_path.stat().st_size > MAX_CONFIG_BYTES:
        raise RuntimeError("Project configuration is unexpectedly large")
    value = json.loads(state_path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise RuntimeError("Project configuration must be a JSON object")
    active = value.get("active_packs")
    if not isinstance(active, dict) or pack_id not in active:
        raise RuntimeError(f"Pack '{pack_id}' is not active for this project")
    selection = active[pack_id]
    if not isinstance(selection, dict):
        raise RuntimeError("Pack selection is malformed")
    host = str(selection.get("host_application", ""))
    hosts = value.get("host_selection")
    if not isinstance(hosts, dict) or hosts.get(host) != pack_id:
        raise RuntimeError(f"Another MCP pack is selected for host '{host}'")
    return selection, state_path


def validate_server(selection: dict[str, Any]) -> tuple[Path, list[str]]:
    server = selection.get("server")
    if not isinstance(server, dict) or not server.get("enabled"):
        raise RuntimeError("External server is not enabled; configure it through a confirmed pack plan")
    executable = Path(str(server.get("executable", "")))
    if not executable.is_absolute() or not executable.is_file():
        raise RuntimeError("Configured external server executable is missing")
    expected = str(server.get("sha256", "")).lower()
    actual = digest_file(executable)
    if len(expected) != 64 or actual != expected:
        raise RuntimeError("External server executable hash does not match the confirmed lock")
    args = server.get("args", [])
    if not isinstance(args, list) or len(args) > 128 or any(not isinstance(item, str) or "\x00" in item for item in args):
        raise RuntimeError("Configured external server arguments are invalid")
    if sum(len(item) for item in args) > 32768:
        raise RuntimeError("Configured external server arguments exceed the safety limit")
    return executable, args


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", required=True)
    parser.add_argument("--doctor", action="store_true")
    args = parser.parse_args()
    try:
        selection, state_path = load_selection(args.pack)
        executable, server_args = validate_server(selection)
        if args.doctor:
            print(json.dumps({
                "healthy": True,
                "pack_id": args.pack,
                "project_configuration": str(state_path),
                "executable": str(executable),
                "sha256": digest_file(executable),
            }, indent=2, sort_keys=True))
            return 0
        # No shell and no environment-sourced command: only the exact executable
        # and arguments protected by the user-confirmed transaction are run.
        os.execv(str(executable), [str(executable), *server_args])
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"AI Game Studio MCP adapter disabled: {exc}", file=sys.stderr)
        return 78
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
