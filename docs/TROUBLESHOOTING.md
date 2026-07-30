# Troubleshooting

## The marketplace or plugin is not visible

Run the exact install commands from the repository root documentation, then start a new task. Use `/plugins` to confirm the marketplace and core plugin are enabled. `/plugins` manages plugins; `/` lists enabled skills.

If the repository default branch or access changed, remove the stale marketplace entry in `/plugins` and add `frabcd/codex-ai-game-studio --ref main` again. Private forks require your own GitHub authentication.

## Skills do not appear in `/`

- Start a new task after enabling/updating the plugin.
- Confirm `ai-game-studio` rather than only an optional pack is enabled.
- Invoke `$ai-game-studio:start` explicitly to distinguish picker caching from a plugin load failure.
- Run `validate skills` and inspect the first malformed skill reported.

IDE integrations may not expose plugin discovery. Use standalone skills as the documented fallback or move to Codex desktop/CLI for bundled hooks and MCP packs.

## Hooks are skipped

Plugin hooks intentionally remain untrusted after installation or changes. Open `/hooks`, inspect the source and exact commands, then trust only the definitions you accept. Changed hashes require review again.

Set `[features] hooks = true` only if hooks were disabled in your own configuration. Enterprise policy may allow managed hooks only; this plugin cannot override that policy.

## An editor pack installs but no editor tools run

Pack MCP entries are inert until setup is planned and digest-confirmed. Run the pack skill or CLI doctor/plan. Check:

- The host application is installed in the detected native OS.
- The pinned upstream server has been approved and installed.
- No second MCP server controls the same host application.
- The editor companion/plugin is enabled and any required localhost port is available.
- The lockfile pin matches the approved transaction.

Do not bridge a Windows GUI editor through WSL paths. Run the editor adapter natively and keep project paths in one path dialect.

## `apply` rejects the digest

This is a safety feature. The plan may be expired, edited, generated for a different environment, or confirmed with a truncated digest. Run `plan` again, compare the full transaction, and confirm the new full digest. Never bypass digest checking.

## Python is not found

Use Python 3.10 or newer when available:

- Windows: `py -3 plugins/ai-game-studio/scripts/ai_game_studio.py doctor`
- macOS/Linux: `python3 plugins/ai-game-studio/scripts/ai_game_studio.py doctor`

The wrappers try common executables and report the commands they attempted. The core uses only the Python standard library.

## GPU/model recommendation is missing

The doctor may not be able to obtain VRAM in a container, remote shell, unsupported driver stack, or privacy-restricted environment. Supply the hardware constraint as a user statement and request a new recommendation. Unknown hardware never implies CUDA compatibility.

Large model downloads require an explicit size/license/hardware/network disclosure. Offline mode returns catalog-compatible manual/CPU alternatives where available.

## Commercial recommendation is blocked

At least one code, weight, dataset, output, reference, identity, voice, or commercial-use field is unknown, custom, conditional, or blocked. Read the linked upstream terms and provide a review decision; do not edit the catalog merely to suppress the block.

## Rollback fails a health check

Stop the affected MCP/editor process, preserve the transaction and backup directories, and run rollback again with the exact plan ID. Do not delete backups manually. If a host application regenerated files after restoration, attach the redacted doctor output, transaction, rollback report, and file list to an issue.

## Offline operation

Catalog search and recommendation are offline by default; only `catalog refresh --online` contacts GitHub. Live stars/releases/activity may be stale or null, but stable capability, platform, risk, license, and documentation fields remain available. An offline core workflow never requires GitHub access.
