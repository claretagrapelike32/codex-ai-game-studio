# Validation evidence

This page is the evidence record for release candidates. Local evidence was
reproduced on Windows on 2026-07-30. The linked public workflows ran against
commit `ed7fd60f570deca1ed11567c9ce7a0967b57f046`.

## Reproduce locally

```text
python tools/validate_repository.py
python tools/run_official_validators.py --require
python -m unittest discover -s tests -p "test_*.py"
python tools/build_release.py --version 1.0.0 --output dist
```

Run the pack transaction smoke test once per pack:

```text
python tools/mock_pack_matrix.py --pack unity
python tools/mock_pack_matrix.py --pack godot
python tools/mock_pack_matrix.py --pack unreal
python tools/mock_pack_matrix.py --pack blender
python tools/mock_pack_matrix.py --pack pixel
```

## Release-candidate record

| Gate | Expected evidence | Status |
|---|---|---|
| Repository contract | Validator log with 85 skills, 49 roles, 12 hook behaviors, 11 rules, 40 templates, and 163 catalog records | **Pass locally** |
| Official plugin validator | Seven validator logs from the pinned official Codex source | **7/7 pass locally** |
| Official skill validator | 85 core logs plus optional-pack skill logs | **92/92 pass locally** |
| Runtime unit tests | Windows, macOS, and Linux CI links | **62/62 pass locally and on all three hosted operating systems** in [CI run 30561154587](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561154587) |
| Hook fixtures | Every supported event fixture on Windows and POSIX command paths | **9/9 pass on Windows, macOS, and Linux** in [CI run 30561154587](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561154587) |
| Pack transaction mocks | Plan, confirmed apply, health check, disable, and rollback for five host packs on three OS runners | **15/15 pass** in [CI run 30561154587](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561154587) |
| Catalog offline fallback | Network-disabled test log and snapshot digest | **Pass locally**; 163 records, source SHA-256 `acdfbb53d66400127f68529e447cc22872a7bc71e5cd994b0f4e32b10c2355a6` |
| Sprite fixture | Transparency, baseline, frame, loop, provenance, and preview evidence | **Pass locally** |
| 3D/PBR fixture | Topology, normals, UV, texture channels, LOD, collision, budget, and multi-view evidence | **Pass locally** |
| Animation fixture | Rig weights, root motion, foot sliding, loop continuity, and preview evidence | **Pass locally** |
| Audio fixture | Peaks, loudness, loop seam, consent, and provenance evidence | **Pass locally** |
| Scene/gameplay fixture | Navigation, lighting, reachable spawn, interaction smoke, frame time, draw calls, and screenshot regression | **Pass locally** |
| Code scanning | Python and GitHub Actions CodeQL analyses | **2/2 pass** in [CodeQL run 30561154579](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561154579) |
| Documentation deployment | Pages build and deployment with public legal/support routes | **Pass** in [Pages run 30561154570](https://github.com/frabcd/codex-ai-game-studio/actions/runs/30561154570) |
| Deterministic release | Two independent build digests, `SHA256SUMS`, SPDX SBOM, and GitHub attestation | **11 files byte-identical locally**; hosted archives build on three operating systems; provenance attestation runs at tag publication |
| Clean installation | Codex CLI and Desktop marketplace install capture | **Pass** from the public `main` snapshot: version `1.0.0`, enabled, **85 skills discovered**; test plugin and marketplace then removed cleanly |

## Clean-install capture

The README's exact commands were run from the Codex Desktop environment against
the public repository. No local-path marketplace was used.

```text
codexVersion: codex-cli 0.146.0-alpha.3.1
marketplaceName: frabcd-ai-game-studio
alreadyAdded: false
pluginId: ai-game-studio@frabcd-ai-game-studio
version: 1.0.0
enabled: true
skillCount: 85
explicitInvocation: AI_GAME_STUDIO_START_LOADED
cleanup marketplacePresent: false
cleanup pluginPresent: false
```

## Before/after asset QA template

Record immutable source and candidate paths. Do not replace the source asset
until a human marks approval.

| Field | Source | Candidate |
|---|---|---|
| Artifact SHA-256 | Pending | Pending |
| Rights/provenance record | Pending | Pending |
| Technical validator output | Pending | Pending |
| Visual/temporal review | Pending | Pending |
| Runtime budget | Pending | Pending |
| Screenshot or preview | Pending | Pending |
| Human decision | Preserve | Pending |

## Universal-directory cases

Attach transcripts for the five positive and three negative review cases listed
in the repository's submission guide. Each transcript must show read-only
detection, one consolidated proposal, license/download/permission disclosure,
explicit digest confirmation, and rollback where a mutation is approved.
