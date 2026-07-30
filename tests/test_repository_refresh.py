from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import refresh_catalog_metadata


class CatalogRefreshTests(unittest.TestCase):
    def make_catalog(self, path: Path) -> None:
        records = [
            {
                "id": f"owner-repository-{index:03d}",
                "repository": {"owner": "owner", "name": f"repository-{index:03d}"},
            }
            for index in range(163)
        ]
        path.write_text(json.dumps({"records": records}), encoding="utf-8")

    def fake_request(self, path: str, token: str):
        self.assertEqual("token-used-but-not-stored", token)
        if path.endswith("/releases/latest"):
            return 404, None
        return 200, {"stargazers_count": 7, "archived": False, "pushed_at": "2026-07-30T00:00:00Z"}

    def test_refresh_writes_only_reviewable_volatile_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-catalog-refresh-") as temporary:
            root = Path(temporary)
            catalog, output = root / "catalog.json", root / "snapshot.json"
            self.make_catalog(catalog)
            with patch.object(refresh_catalog_metadata, "request_json", side_effect=self.fake_request):
                result = refresh_catalog_metadata.refresh(catalog, output, "token-used-but-not-stored")
            self.assertEqual(163, len(result["records"]))
            self.assertEqual(
                {"id", "stars", "archived", "latest_release", "last_activity", "retrieval"},
                set(result["records"][0]),
            )
            self.assertEqual("github-api", result["records"][0]["retrieval"])
            self.assertNotIn("token-used-but-not-stored", output.read_text(encoding="utf-8"))

    def test_failure_does_not_publish_partial_snapshot(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-catalog-failure-") as temporary:
            root = Path(temporary)
            catalog, output = root / "catalog.json", root / "snapshot.json"
            self.make_catalog(catalog)
            with patch.object(refresh_catalog_metadata, "request_json", side_effect=RuntimeError("API unavailable")):
                with self.assertRaises(RuntimeError):
                    refresh_catalog_metadata.refresh(catalog, output, "token-used-but-not-stored")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
