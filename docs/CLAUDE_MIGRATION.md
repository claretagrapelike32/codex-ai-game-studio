# Claude-to-Codex migration map

The migration command is conservative: it produces a plan first, supports dual-tool repositories, and leaves Claude files in place unless removal is separately approved.

```text
python plugins/ai-game-studio/scripts/ai_game_studio.py migrate claude --project .
```

| Claude-oriented source | Codex destination | Transformation |
|---|---|---|
| Root `CLAUDE.md` | Root `AGENTS.md` | Preserve project guidance; replace Claude commands/tools with behavior and namespaced skills |
| Path rules | Nested/path-scoped `AGENTS.md` | Generate only where the rule has a real subtree scope |
| `.claude/agents/*.md` | `.codex/agents/*.toml` | Keep role/description/instructions; remove fixed model, unsupported tools, memory, and turn limits |
| Slash commands | `$plugin:skill` references | Route to installed Codex skills; no deprecated custom prompt aliases |
| Claude skills | Codex `SKILL.md` + `agents/openai.yaml` | Frontmatter only `name`/`description`; add UI metadata and invocation policy |
| Hook scripts/settings | `hooks/hooks.json` + cross-platform Python | Map to supported Codex events, `PLUGIN_ROOT`/`PLUGIN_DATA`, `commandWindows`, trust through `/hooks` |
| Status line | Session-start summary + `sprint-status` | Avoid unsupported continuous status-line behavior |
| Claude tool allowlists | Behavior-based permissions | Inherit active Codex model and permission mode; request approval where required |

## Event mapping

| Upstream behavior | Codex event |
|---|---|
| Orientation and gap detection | `SessionStart` |
| Agent start/stop logging | `SubagentStart`, `SubagentStop` |
| State preservation around compaction | `PreCompact`, `PostCompact` |
| Commit/push safeguards | `PreToolUse` |
| Asset and skill validation | `PostToolUse` |
| Session summary, archive hint, best-effort notification | `Stop`, `SessionEnd` |

## Plan contents

The migration plan lists every source, destination, status (`ported`, `replaced`, or genuinely `not-applicable`), digest, backup, and validation. Colliding `AGENTS.md`, `.codex`, or agent names are not overwritten automatically. The user chooses merge, rename, skip, or replace before a new plan is generated.

## Runtime negative scan

Generated runtime files must not contain `.claude/` paths, `/skill` invocation instructions, Claude-only tool declarations, fixed `opus`/`sonnet`/`haiku` models, memory fields, or fixed maximum turns. Historical provenance files and this migration documentation may name Claude explicitly.

## Rollback

Rollback restores every shared file from a content-addressed backup and removes only files created by the confirmed transaction. It does not delete the original Claude configuration, remove commits, reset branches, or touch unrelated dirty files.
