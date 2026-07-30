#!/usr/bin/env python3
"""Refresh volatile GitHub catalog metadata into a review-only snapshot."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API = "https://api.github.com"


def request_json(path: str, token: str) -> tuple[int, Any]:
    request = Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "frabcd-codex-ai-game-studio-catalog-refresh",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return 404, None
        body = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"GitHub API {exc.code} for {path}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"GitHub API request failed for {path}: {exc.reason}") from exc


def refresh(catalog_path: Path, output: Path, token: str, delay: float = 0.0) -> dict[str, Any]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    records = catalog.get("records")
    if not isinstance(records, list) or len(records) != 163:
        raise ValueError("stable catalog must contain exactly 163 records")
    refreshed: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict) or not isinstance(record.get("repository"), dict):
            raise ValueError(f"catalog record {index} is malformed")
        repo = record["repository"]
        owner, name = repo.get("owner"), repo.get("name")
        if not isinstance(owner, str) or not isinstance(name, str):
            raise ValueError(f"catalog record {index} has no owner/name")
        status, metadata = request_json(f"/repos/{owner}/{name}", token)
        if status != 200 or not isinstance(metadata, dict):
            raise RuntimeError(f"repository not found during refresh: {owner}/{name}")
        release_status, release = request_json(f"/repos/{owner}/{name}/releases/latest", token)
        latest_release = release.get("tag_name") if release_status == 200 and isinstance(release, dict) else None
        refreshed.append(
            {
                "id": record.get("id"),
                "stars": metadata.get("stargazers_count"),
                "archived": metadata.get("archived"),
                "latest_release": latest_release,
                "last_activity": metadata.get("pushed_at"),
                "retrieval": "github-api",
            }
        )
        if delay and index != len(records):
            time.sleep(delay)
    snapshot_date = datetime.now(timezone.utc).date().isoformat()
    snapshot = {
        "$schema": "https://frabcd.github.io/codex-ai-game-studio/schemas/catalog-snapshot.schema.json",
        "schema_version": "1.0.0",
        "snapshot_date": snapshot_date,
        "source": "GitHub REST API metadata; review before merge. This is not a license grant or install authorization.",
        "records": refreshed,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return snapshot


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=root / "plugins" / "ai-game-studio" / "catalog" / "catalog.json",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--delay", type=float, default=0.0)
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required; the token value is never printed")
    date = datetime.now(timezone.utc).date().isoformat()
    output = args.output or args.catalog.parent / "snapshots" / f"github-{date}.json"
    snapshot = refresh(args.catalog.resolve(), output.resolve(), token, max(0.0, args.delay))
    print(json.dumps({"output": str(output), "record_count": len(snapshot["records"]), "snapshot_date": date}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
