# Upgrade guide

## Before upgrading

1. Finish or rollback active transactions.
2. Commit or otherwise back up project-owned `.ai-game-studio/project.json` and `lock.json` if your team tracks them.
3. Record enabled optional packs and run `doctor`.
4. Review the release notes for schema, hook, pack-pin, permission, and migration changes.

Use `/plugins` to refresh the `frabcd-ai-game-studio` marketplace and update selected plugins. Start a new task afterward so skill and hook metadata reload.

## Core compatibility

Patch releases preserve schemas and command behavior. Minor releases may add optional fields and skills. A major release may require a generated migration plan. The CLI refuses to rewrite a newer unknown project/lock schema.

## Hook changes

Codex trust is tied to a hook definition's hash. After an automation-pack update, use `/hooks` to review changed commands before trusting them. An update does not preserve trust for modified hook code.

## Pack pin changes

Plugin updates can recommend a newer upstream MCP but cannot silently change a project's lock. Run `pack doctor` and `pack plan`; review upstream license, permissions, download, and compatibility differences, then confirm the new digest. Rollback retains the prior pin and config backup.

## Catalog changes

Volatile metadata snapshots do not change a project's locked dependency. Stable curation changes are reviewed in pull requests and can make a prior commercial recommendation conditional or blocked. Re-run recommendation before a release milestone.

## Downgrade

Use `/plugins` to select a prior marketplace/plugin release where available, then restore compatible project/lock files from version control. Do not hand-edit schema versions or transaction digests. Optional external tools may require their own supported downgrade procedure.
