---
layout: default
title: Unity Pack
permalink: /packs/unity/
---

# Unity pack

Default upstream: [`CoplayDev/unity-mcp`](https://github.com/CoplayDev/unity-mcp). The IvanMurzak implementation remains a selectable inactive alternative.

```text
codex plugin add ai-game-studio-unity@frabcd-ai-game-studio
```

The setup skill detects `ProjectVersion.txt`, package state, installed editors, OS boundary, and existing MCP conflicts. It plans a pinned server plus editor companion, discloses process/network/project-write permissions, and validates compilation, connection, tests, and a screenshot after confirmation. Disable stops the adapter; rollback restores Codex and Unity package/config backups.

Exact pins and commands live in the pack descriptor shipped with the plugin.
