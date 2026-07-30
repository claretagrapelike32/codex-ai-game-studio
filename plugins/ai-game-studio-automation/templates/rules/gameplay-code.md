# Gameplay Code path-scoped AGENTS.md fragment

> Adapted from the pinned upstream source at `984023ddac0d5e27624f2baacde6105e45de375f` under MIT; exact path and blob are in the parity ledger.

This template is inert until the automation pack shows the destination files and the user confirms materialization. Merge it into the nearest path-scoped `AGENTS.md` covering:

- `src/gameplay/**`

# Gameplay Code Rules

- ALL gameplay values MUST come from external config/data files, NEVER hardcoded
- Use delta time for ALL time-dependent calculations (frame-rate independence)
- NO direct references to UI code — use events/signals for cross-system communication
- Every gameplay system must implement a clear interface
- State machines must have explicit transition tables with documented states
- Write unit tests for all gameplay logic — separate logic from presentation
- Document which design doc each feature implements in code comments
- No static singletons for game state — use dependency injection

## Examples

**Correct** (data-driven):

```gdscript
var damage: float = config.get_value("combat", "base_damage", 10.0)
var speed: float = stats_resource.movement_speed * delta
```

**Incorrect** (hardcoded):

```gdscript
var damage: float = 25.0   # VIOLATION: hardcoded gameplay value
var speed: float = 5.0      # VIOLATION: not from config, not using delta
```
