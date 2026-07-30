# Production recipes

The 12 descriptors in this directory define ordered, reversible game-production
workflows. They declare inputs, capabilities, expected artifacts, fallbacks,
provenance outputs, and quality gates for rights, formats, visual and temporal
consistency, runtime budgets, playability, regression evidence, and human
approval.

Recipes are plans, not executable installers. Every mutating workflow uses the
`plan-confirmed-digest-before-apply` policy, preserves source assets, and waits
for human approval before a generated candidate replaces production content.
