# Game code scope

Keep engine-facing changes small and reversible. Preserve serialization formats and editor metadata. Run the narrowest compile, static analysis, smoke test, and representative gameplay check available.

Do not silently add packages, editor plugins, global tools, network listeners, or generated binaries. Route those through the confirmed transaction workflow and record exact dependency pins in `.ai-game-studio/lock.json`.

For performance-sensitive work, report frame-time, allocations, memory, draw calls, and asset-budget effects when the engine exposes them.
