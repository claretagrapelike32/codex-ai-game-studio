# Claude Code Game Studios parity ledger

Pinned source: [https://github.com/Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) at `984023ddac0d5e27624f2baacde6105e45de375f` (MIT).

The JSON ledger is the release authority. A status of `ported` means the behavior and content were adapted to Codex-native files; `replaced` means an unsupported runtime mechanism was mapped to a supported Codex behavior. There are no `not-applicable` entries in v1.

| Surface | Source | v1 status |
|---|---:|---:|
| Skills | 73 | 73 ported |
| Roles | 49 | 49 ported |
| Hook behaviors | 12 | 12 replaced |
| Path rules | 11 | 11 ported |
| Templates actually present | 40 | 40 ported |
| New generative skills | 0 | 12 native |

Every derived entry records its upstream path, commit, Git blob SHA, destination, status, and acceptance tests in `ledger.json`.
