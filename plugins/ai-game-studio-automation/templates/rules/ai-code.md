# Ai Code path-scoped AGENTS.md fragment

> Adapted from the pinned upstream source at `984023ddac0d5e27624f2baacde6105e45de375f` under MIT; exact path and blob are in the parity ledger.

This template is inert until the automation pack shows the destination files and the user confirms materialization. Merge it into the nearest path-scoped `AGENTS.md` covering:

- `src/ai/**`

# AI Code Rules

- AI update budget: 2ms per frame maximum — profile to verify
- All AI parameters must be tunable from data files (behavior tree weights, perception ranges, timers)
- AI must be debuggable: implement visualization hooks for all AI state (paths, perception cones, decision trees)
- AI should telegraph intentions — players need time to read and react
- Prefer utility-based or behavior tree approaches over hard-coded if/else chains
- Group AI must support formation, flanking, and role assignment from data
- All AI state machines must log transitions for debugging
- Never trust AI input from the network without validation
