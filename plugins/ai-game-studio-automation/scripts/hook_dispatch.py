#!/usr/bin/env python3
"""Bounded, privacy-preserving Codex lifecycle hooks.

The dispatcher consumes the official JSON event object on stdin.  It never
reads credential values or transcript bodies and caps every persisted record.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping


MAX_INPUT_BYTES = 1024 * 1024
MAX_RECORD_BYTES = 16 * 1024
MAX_LOG_BYTES = 1024 * 1024
KEEP_LOG_BYTES = 512 * 1024
BEHAVIORS = (
    "detect-gaps",
    "log-agent",
    "log-agent-stop",
    "notify",
    "post-compact",
    "pre-compact",
    "session-start",
    "session-stop",
    "validate-assets",
    "validate-commit",
    "validate-push",
    "validate-skill-change",
)
SAFE_FIELDS = (
    "session_id",
    "turn_id",
    "hook_event_name",
    "model",
    "permission_mode",
    "source",
    "reason",
    "trigger",
    "agent_id",
    "agent_type",
    "tool_name",
    "tool_use_id",
    "stop_hook_active",
)


def read_event() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("hook input exceeded 1 MiB")
    value = json.loads(raw or b"{}")
    if not isinstance(value, dict):
        raise ValueError("hook input must be an object")
    return value


def data_root() -> Path | None:
    value = os.environ.get("PLUGIN_DATA")
    if not value:
        return None
    root = Path(value).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def bounded_append(path: Path, record: Mapping[str, Any]) -> None:
    encoded = (json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    if len(encoded) > MAX_RECORD_BYTES:
        encoded = (json.dumps({"event": record.get("event"), "truncated": True}) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size + len(encoded) > MAX_LOG_BYTES:
        with path.open("rb") as handle:
            handle.seek(max(0, path.stat().st_size - KEEP_LOG_BYTES))
            tail = handle.read()
        newline = tail.find(b"\n")
        if newline >= 0:
            tail = tail[newline + 1 :]
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_bytes(tail)
        os.replace(temp, path)
    with path.open("ab") as handle:
        handle.write(encoded)


def audit(event: Mapping[str, Any], *, behavior: str, details: Mapping[str, Any] | None = None) -> None:
    root = data_root()
    if root is None:
        return
    record = {field: event.get(field) for field in SAFE_FIELDS if field in event}
    record.update({"event": event.get("hook_event_name"), "behavior": behavior})
    if details:
        record["details"] = dict(details)
    bounded_append(root / "audit" / "events.jsonl", record)


def emit(value: Mapping[str, Any] | None = None) -> None:
    if value is not None:
        print(json.dumps(value, ensure_ascii=False))


def additional(event_name: str, text: str) -> dict[str, Any]:
    return {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": text[:3000]}}


def project_gaps(cwd: Path) -> list[str]:
    gaps: list[str] = []
    if not (cwd / ".ai-game-studio" / "project.json").is_file():
        gaps.append("AI Game Studio is not configured for this project")
    if not (cwd / "AGENTS.md").is_file():
        gaps.append("no root AGENTS.md was detected")
    if not (cwd / ".git").exists():
        gaps.append("the current directory is not a Git worktree root")
    return gaps


def session_start(event: Mapping[str, Any]) -> None:
    cwd = Path(str(event.get("cwd") or ".")).resolve()
    gaps = project_gaps(cwd)
    audit(event, behavior="session-start", details={"gap_count": len(gaps)})
    audit(event, behavior="detect-gaps", details={"gaps": gaps})
    summary = "Codex AI Game Studio automation is active. Hooks are advisory and project mutation still requires a confirmed transaction digest."
    if gaps:
        summary += " Detected: " + "; ".join(gaps) + ". Use $ai-game-studio:toolchain-doctor for a read-only proposal."
    emit(additional("SessionStart", summary))


def agent_event(event: Mapping[str, Any], behavior: str) -> None:
    audit(event, behavior=behavior)
    if event.get("hook_event_name") == "SubagentStart":
        emit(additional("SubagentStart", "Keep this subagent bounded to its assigned files and return verification evidence."))
    else:
        # SubagentStop requires JSON on successful exit.
        emit({})


def compact_event(event: Mapping[str, Any], before: bool) -> None:
    behavior = "pre-compact" if before else "post-compact"
    audit(event, behavior=behavior)
    root = data_root()
    state = {
        "session_id": event.get("session_id"),
        "turn_id": event.get("turn_id"),
        "trigger": event.get("trigger"),
        "permission_mode": event.get("permission_mode"),
        "note": "Project mutations require a current confirmed transaction digest.",
    }
    if before and root is not None:
        target = root / "state" / "pre-compact.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, target)
        emit({})
    elif not before:
        emit(additional("PostCompact", "Restored safety state: inspect and plan first; apply only a current user-confirmed transaction digest."))


def tool_command(event: Mapping[str, Any]) -> str:
    value = event.get("tool_input")
    if isinstance(value, dict) and isinstance(value.get("command"), str):
        return value["command"]
    return ""


def deny_pre_tool(reason: str) -> None:
    emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })


def project_state_errors(cwd: Path) -> list[str]:
    state_root = next((candidate / ".ai-game-studio" for candidate in (cwd, *cwd.parents) if (candidate / ".ai-game-studio").exists()), None)
    if state_root is None:
        return []
    errors: list[str] = []
    for name in ("project.json", "lock.json"):
        path = state_root / name
        if not path.is_file():
            errors.append(f"{name} is missing")
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(value, dict):
                errors.append(f"{name} must contain an object")
        except (OSError, json.JSONDecodeError):
            errors.append(f"{name} is invalid JSON")
    return errors


def current_git_branch(cwd: Path) -> str | None:
    git_entry: Path | None = None
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            git_entry = candidate / ".git"
            break
    if git_entry is None:
        return None
    if git_entry.is_file():
        try:
            value = git_entry.read_text(encoding="utf-8", errors="replace").strip()
            if value.lower().startswith("gitdir:"):
                location = Path(value.split(":", 1)[1].strip())
                git_entry = location if location.is_absolute() else (git_entry.parent / location).resolve()
        except OSError:
            return None
    try:
        head = (git_entry / "HEAD").read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    prefix = "ref: refs/heads/"
    return head[len(prefix) :] if head.startswith(prefix) else None


def pre_tool(event: Mapping[str, Any]) -> None:
    command = tool_command(event)
    normalized = re.sub(r"\s+", " ", command.strip()).lower()
    cwd = Path(str(event.get("cwd") or ".")).resolve()
    if re.search(r"\bgit\s+commit\b", normalized):
        state_errors = project_state_errors(cwd)
        audit(event, behavior="validate-commit", details={"no_verify": "--no-verify" in normalized, "state_errors": len(state_errors)})
        if "--no-verify" in normalized:
            deny_pre_tool("Commit safeguard: --no-verify bypasses project validation. Run validators or obtain explicit project-owner approval.")
            return
        if state_errors:
            deny_pre_tool("Commit safeguard: " + "; ".join(state_errors) + ". Repair or roll back the project transaction first.")
            return
    if re.search(r"\bgit\s+push\b", normalized):
        force = bool(re.search(r"(?:^|\s)(?:--force(?:-with-lease)?|-f)(?:\s|$)", normalized)) or "+refs/" in normalized
        branch = current_git_branch(cwd)
        bare_push = bool(re.fullmatch(r".*\bgit\s+push(?:\s+origin)?\s*", normalized))
        protected = bool(re.search(r"\b(?:origin\s+)?(?:main|master)(?::|\s|$)", normalized)) or (bare_push and branch in {"main", "master"})
        audit(event, behavior="validate-push", details={"force": force, "protected_branch": protected})
        if force:
            deny_pre_tool("Push safeguard: force pushes are blocked. Use a reviewable branch and a normal push.")
            return
        if protected:
            deny_pre_tool("Push safeguard: direct pushes to main/master are blocked. Push a feature branch and open a pull request.")
            return
    emit({})


def changed_paths(event: Mapping[str, Any]) -> list[Path]:
    command = tool_command(event)
    values: list[str] = []
    patterns = (
        r"(?m)^\*{3} (?:Add|Update) File:\s*(.+)$",
        r"(?m)^\+\+\+\s+b/(.+)$",
    )
    for pattern in patterns:
        values.extend(match.strip() for match in re.findall(pattern, command))
    cwd = Path(str(event.get("cwd") or ".")).resolve()
    result: list[Path] = []
    for value in values[:100]:
        path = Path(value.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            continue
        resolved = (cwd / path).resolve()
        try:
            resolved.relative_to(cwd)
        except ValueError:
            continue
        result.append(resolved)
    return result


def validate_skill(path: Path) -> list[str]:
    if path.name != "SKILL.md" or not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return [f"{path}: missing YAML frontmatter"]
    front = text[4 : text.find("\n---\n", 4)]
    keys = {line.split(":", 1)[0].strip() for line in front.splitlines() if ":" in line}
    errors = []
    if keys != {"name", "description"}:
        errors.append(f"{path}: frontmatter must contain only name and description")
    if not (path.parent / "agents" / "openai.yaml").is_file():
        errors.append(f"{path}: agents/openai.yaml is missing")
    return errors


def validate_asset(path: Path) -> list[str]:
    extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".glb", ".gltf", ".fbx", ".wav", ".ogg", ".mp3"}
    if path.suffix.lower() not in extensions or not path.is_file():
        return []
    errors: list[str] = []
    size = path.stat().st_size
    if size == 0:
        errors.append(f"{path}: asset is empty")
    if size > 250 * 1024 * 1024:
        errors.append(f"{path}: asset exceeds the 250 MiB project guardrail")
    if path.suffix.lower() == ".png" and path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        errors.append(f"{path}: invalid PNG signature")
    if path.suffix.lower() == ".glb" and path.read_bytes()[:4] != b"glTF":
        errors.append(f"{path}: invalid GLB signature")
    return errors


def post_tool(event: Mapping[str, Any]) -> None:
    paths = changed_paths(event)
    errors: list[str] = []
    skill_paths = [path for path in paths if path.name == "SKILL.md"]
    asset_paths = [path for path in paths if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".glb", ".gltf", ".fbx", ".wav", ".ogg", ".mp3"}]
    for path in skill_paths:
        errors.extend(validate_skill(path))
    for path in asset_paths:
        errors.extend(validate_asset(path))
    if skill_paths:
        audit(event, behavior="validate-skill-change", details={"files": len(skill_paths), "errors": len(errors)})
    if asset_paths:
        audit(event, behavior="validate-assets", details={"files": len(asset_paths), "errors": len(errors)})
    if errors:
        message = "Post-change validation found: " + "; ".join(errors[:8])
        emit({"decision": "block", "reason": message, **additional("PostToolUse", message)})
    else:
        emit({})


def stop_event(event: Mapping[str, Any]) -> None:
    audit(event, behavior="session-stop")
    audit(event, behavior="notify", details={"delivery": "plugin-data-jsonl"})
    root = data_root()
    if root is not None:
        bounded_append(root / "notifications.jsonl", {
            "event": event.get("hook_event_name"),
            "session_id": event.get("session_id"),
            "turn_id": event.get("turn_id"),
            "status": "completed",
        })
    # Stop requires valid JSON; SessionEnd ignores output, but {} is harmless.
    emit({})


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    mode = args[0] if args else "auto"
    try:
        event = read_event()
        event_name = str(event.get("hook_event_name") or mode)
        if event_name == "SessionStart":
            session_start(event)
        elif event_name == "SubagentStart":
            agent_event(event, "log-agent")
        elif event_name == "SubagentStop":
            agent_event(event, "log-agent-stop")
        elif event_name == "PreCompact":
            compact_event(event, True)
        elif event_name == "PostCompact":
            compact_event(event, False)
        elif event_name == "PreToolUse":
            pre_tool(event)
        elif event_name == "PostToolUse":
            post_tool(event)
        elif event_name in {"Stop", "SessionEnd"}:
            stop_event(event)
        else:
            emit({})
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        # Hooks are safety aids rather than a complete enforcement boundary.
        # Malformed input is surfaced but does not reveal raw event contents.
        print(json.dumps({"systemMessage": f"AI Game Studio hook could not process the event: {type(exc).__name__}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
