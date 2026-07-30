---
layout: default
title: Automation Pack
permalink: /automation/
---

# AI Game Studio Automation

The optional automation plugin provides reviewed lifecycle hooks, project-role installation, scoped `AGENTS.md` generation, and Claude-project migration. It is not part of the universal core because hook commands and project setup can write local files.

```text
codex plugin add ai-game-studio-automation@frabcd-ai-game-studio
```

After installation, start a new task. Review bundled hooks with `/hooks`; they do not run until you trust their exact current definitions.

```text
$ai-game-studio-automation:setup-automation Inspect this repository, select common
roles plus only its engine specialists, and show the proposed AGENTS.md, TOML
agents, rules, backups, and rollback before writing.
```

Project materialization always begins with a transaction plan and full file preview. Roles inherit the current Codex model and permission mode. The installer removes unsupported fixed models, tool allowlists, memory fields, and turn limits.
