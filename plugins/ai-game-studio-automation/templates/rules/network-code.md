# Network Code path-scoped AGENTS.md fragment

> Adapted from the pinned upstream source at `984023ddac0d5e27624f2baacde6105e45de375f` under MIT; exact path and blob are in the parity ledger.

This template is inert until the automation pack shows the destination files and the user confirms materialization. Merge it into the nearest path-scoped `AGENTS.md` covering:

- `src/networking/**`

# Network Code Rules

- Server is AUTHORITATIVE for all gameplay-critical state — never trust the client
- All network messages must be versioned for forward/backward compatibility
- Client predicts locally, reconciles with server — implement rollback for mispredictions
- Handle disconnection, reconnection, and host migration gracefully
- Rate-limit all network logging to prevent log flooding
- All networked values must specify replication strategy: reliable/unreliable, frequency, interpolation
- Bandwidth budget: define and track per-message-type bandwidth usage
- Security: validate all incoming packet sizes and field ranges
