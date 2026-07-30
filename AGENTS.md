# Codex AI Game Studio contributor instructions

These instructions apply to the whole repository.

- Preserve the safety contract: read-only detection, one exact plan, explicit full-digest confirmation, scoped apply, validation, and rollback. Never combine plan and mutation.
- Keep the universal core usable offline and free of required MCP servers, hosted backends, external downloads, or non-standard Python dependencies.
- Treat catalog entries as untrusted metadata. Never clone, install, import, or execute a catalog repository during validation.
- Keep stable curation separate from volatile GitHub metadata. Never infer a license or platform claim from popularity.
- Store credential environment-variable names only. Tests and fixtures must contain no usable secret values.
- Use tokenized argument arrays and resolved, bounded paths for executable actions. No curl-pipe-shell, floating executable dependency, broad recursive deletion, or hidden host-application control.
- Preserve exact release counts: 73 source skills + 12 new skills, 49 roles, 12 hook behaviors, 11 rules, 40 upstream templates, and 163 catalog records.
- Skill frontmatter contains only `name` and `description`; every skill includes `agents/openai.yaml`. Setup, install, engine-control, refresh, and destructive enhancement skills disable implicit invocation.
- Hooks consume official JSON on stdin, emit bounded/redacted JSON, use `PLUGIN_ROOT`/`PLUGIN_DATA`, provide `commandWindows`, and remain trust-gated.
- Run the relevant standard-library unit tests and validators. Tests must use temporary directories and mocked editors/MCP servers.
- Update documentation, provenance/attribution, schemas, tests, and `CHANGELOG.md` when a public contract changes.
