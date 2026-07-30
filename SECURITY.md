# Security policy

## Supported versions

Security fixes are provided for the latest released major version. During the v1 preview, `1.x` is supported.

## Report a vulnerability

Please use GitHub's **Report a vulnerability** private security-advisory form for this repository. Do not post exploitable details in a public issue or Discussion. Include:

- Affected version, plugin, skill, command, or pack.
- Operating system and execution surface.
- Reproduction steps and the smallest safe proof of concept.
- Expected versus actual permission, plan, digest, backup, or rollback behavior.
- Whether credentials, arbitrary process execution, path escape, or editor control may be involved.

You should receive an acknowledgement within seven days. Coordinated disclosure timing will be agreed after triage. There is no paid bug-bounty program.

## Security boundaries

- The core plugin has no hosted backend and does not require credentials.
- Catalog metadata is not trusted executable code.
- External installations and model downloads require an unexpired, digest-confirmed transaction.
- Paths are resolved and checked against the intended project/plugin data roots before writes, backups, or rollback.
- Hooks are opt-in and require explicit trust in `/hooks`.
- MCP servers are external local processes with their own security models; one server per host application is allowed.
- Secrets must be supplied through documented environment variables or the external provider's secure login flow. The project never requests secret values in prompts or stores them in plans, catalogs, logs, fixtures, or provenance.

## Out of scope

Vulnerabilities in an external engine, DCC application, model, repository, package registry, or MCP server should be reported to that upstream project. If the catalog metadata or adapter exposes users to it, also report the integration impact here.
