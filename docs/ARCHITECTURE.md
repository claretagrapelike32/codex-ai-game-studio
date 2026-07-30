# Architecture

## Design goals

Codex AI Game Studio is deliberately a **skill-first plugin plus optional local packs**, not a mega-MCP that launches every catalog entry. The core must work offline, remain useful without an editor bridge, and never turn discovery into execution.

```mermaid
flowchart TD
    U["User outcome"] --> R["$ai-game-studio:start router"]
    R --> S["Focused skill or recipe"]
    S --> D["Read-only doctor"]
    D --> C["Stable offline catalog"]
    D --> V["Optional live metadata"]
    C --> P["Deterministic transaction plan"]
    V --> P
    P --> H{"Human confirms digest"}
    H -- "No / expired / changed" --> N["No mutation"]
    H -- "Yes" --> A["Scoped apply"]
    A --> Q["Health and quality gates"]
    Q --> L["Project state, lock, evidence, rollback"]
    A -. "only when selected" .-> M["One editor MCP per host"]
```

## Packages

| Package | Trust level | Responsibility |
|---|---|---|
| `ai-game-studio` | Universal core | 85 skills, catalog, recipes, read-only doctor, plan/validation CLI |
| `ai-game-studio-automation` | Optional local | Hooks, project-role materialization, scoped `AGENTS.md`, migration |
| Engine/DCC/pixel packs | Optional local | Inert adapter, one pinned upstream MCP, conflict checks, plan/apply/rollback |
| External catalog entries | Never bundled | Models, weights, libraries, applications, benchmarks, and tools selected per workflow |

Each plugin owns a valid `.codex-plugin/plugin.json`; the repository marketplace at `.agents/plugins/marketplace.json` controls ordering and availability. Core skills are discoverable through `/` and explicitly invoked as `$ai-game-studio:<skill>`.

## Runtime layers

### Skill layer

Skills classify intent, preserve creative context, choose recipes, request material decisions, and interpret validation evidence. `start` is the main router; `help` recommends the next workflow based on project state. Long prompt patterns and domain references stay outside frontmatter.

### Deterministic layer

The standard-library Python CLI owns facts that should not vary with model reasoning:

```text
doctor
catalog search|recommend|refresh
pack doctor|plan|apply|disable|rollback
migrate claude
validate plugin|skills|catalog|parity|platform
```

PowerShell and POSIX wrappers locate an appropriate Python 3 executable and delegate to the same implementation. No Git Bash is required on Windows.

### Data layer

- `catalog/catalog.json`: stable, human-reviewed curation.
- `catalog/snapshots/*.json`: volatile GitHub stars/releases/activity/archive snapshots.
- `recipes/*.json`: ordered production stages, artifacts, capabilities, fallbacks, provenance, rollback, and gates.
- `packs/*.json`: host, platforms, source pin, tokenized command/arguments, conflicts, permissions, health checks, uninstall, and rollback.
- `.ai-game-studio/project.json`: selected project policy and workflow choices.
- `.ai-game-studio/lock.json`: exact external dependency pins and transaction state.

## Transaction protocol

A mutating operation cannot construct and apply actions in one step.

1. `plan` detects the environment again and canonicalizes a transaction.
2. The transaction includes an ID, timestamps/expiry, exact actions, downloads, licenses, permissions, backups, rollback operations, and detected environment.
3. A SHA-256 digest is computed over canonical JSON excluding the digest field.
4. The user reviews the rendered proposal and confirms that digest.
5. `apply` reloads the plan, verifies the digest/expiry/environment assumptions, then performs only listed operations.
6. Health checks and quality gates run. Failure triggers a bounded rollback offer; it never broadens the plan.

Backups live under the active project or plugin data root, not a broad home/workspace target. Resolved paths are checked before copy, removal, or restoration.

## Catalog routing

Live metadata is optional and never overrides stable curation. When online freshness is requested, routing is GitHub connector → authenticated `gh` → public GitHub API → offline snapshot. The weekly Action updates the volatile snapshot on a review branch and opens a pull request.

Recommendation filters are hard constraints first: license/commercial status, OS/architecture, host application, GPU/VRAM, authentication/privacy, permissions, download size, and maturity. Quality/cost/performance comparisons happen only among compatible candidates.

## MCP boundary

Pack `.mcp.json` entries call a bundled inert adapter. On first use it reports that setup is unconfirmed and points to `doctor`/`plan`; it does not fetch or launch upstream code. After a confirmed apply, the adapter resolves the exact lockfile pin and starts the approved local server. Conflicting servers for the same host block activation.

Local servers should use stdio or localhost. Remote exposure, non-loopback binding, broad filesystem access, secret forwarding, and editor writes require explicit disclosure and confirmation.

## Hook boundary

The automation plugin's `hooks/hooks.json` maps 12 upstream behaviors onto supported Codex events. Commands receive official JSON on stdin and use `PLUGIN_ROOT` plus `PLUGIN_DATA`; `commandWindows` avoids POSIX assumptions. Logs are bounded, structured, and redacted. Plugin hooks do not run until the user reviews and trusts them with `/hooks`.

## Quality evidence

Recipes produce artifacts before claims: format validator reports, contact sheets/turntables, temporal overlays, profiler captures, smoke-test logs, screenshot diffs, provenance manifests, and human approval records. Enhancement is candidate-based; source replacement is a separate approved action.
