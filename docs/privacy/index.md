---
layout: default
title: Privacy Notice
permalink: /privacy/
---

# Privacy notice

**Publisher-review draft — 2026-07-30**

This notice describes the Codex AI Game Studio software distributed by `frabcd`. It should be reviewed by the publisher before universal-directory submission.

## Core plugin

The core plugin has **no hosted backend operated by this project**. The project owner does not receive your prompts, source code, assets, catalog searches, machine inventory, plans, lockfiles, test results, or generated outputs through a project-operated service. The core contains local skills, reference data, recipes, and standard-library Python helpers.

Your use of Codex and any OpenAI-hosted features is governed by the privacy terms for the OpenAI product and workspace through which you run the plugin.

## Local inspection and storage

The read-only doctor may inspect operating-system and architecture identifiers, project markers and versions, installed application/runtime names and versions, configured MCP **server names**, GPU backend and reported VRAM, free disk, network requirements, and whether named credential environment variables exist. It does not read or emit the values of those credential variables.

Confirmed workflows may store:

- Project choices in `.ai-game-studio/project.json`.
- Exact dependency pins and transaction state in `.ai-game-studio/lock.json`.
- Plans, backups, validation evidence, and rollback receipts in project-scoped or plugin-data directories.
- Bounded, redacted automation logs under `PLUGIN_DATA` when the optional automation plugin and trusted hooks are enabled.

You control these local files through your filesystem, version-control, backup, and retention policies. Rollback does not automatically remove audit evidence unless the transaction says so.

## Network requests

Offline catalog use makes no live GitHub request. If you request current repository metadata, the workflow may use your installed GitHub connector, authenticated `gh`, or public GitHub endpoints. GitHub receives the normal request metadata and any authentication that your own connector or CLI supplies; this project does not receive it.

Optional tools can send prompts, reference images, audio, 3D assets, project data, or generated output to their own local or hosted services. Before activation, the transaction must disclose network destinations, data categories, credential variable names, and known privacy documentation. Those third parties govern their own collection, retention, model training, and deletion behavior.

## Credentials and sensitive data

Do not paste API keys, tokens, private keys, `.env` contents, unreleased proprietary assets, biometric/identity data, or unconsented voice recordings into public issues, Discussions, fixtures, catalog records, plans, or provenance files. The software detects credential presence by variable name only and redacts known secret-shaped values from its own logs.

Voice or identity workflows require documented authority and consent. A missing consent/rights record blocks production use.

## Website

The GitHub Pages documentation is a static site. This project does not add its own analytics, advertising, tracking pixels, accounts, or cookies. GitHub may process normal hosting and access information under GitHub's own privacy terms.

## Children

The software is a developer tool and is not directed to children. Do not use it to collect personal data from minors without appropriate authority and safeguards.

## Changes and contact

Material changes will be recorded in the repository history and changelog with an updated date. For a privacy question, contact the publisher through the GitHub profile at [github.com/frabcd](https://github.com/frabcd). Do not include sensitive project data in a public message.
