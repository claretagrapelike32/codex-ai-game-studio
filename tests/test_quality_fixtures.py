from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "tests" / "fixtures" / "quality" / "representative-quality-evidence.json"
SPRITE_VISUAL = ROOT / "assets" / "examples" / "sprite-before-after.svg"
DOC_EVIDENCE = ROOT / "docs" / "assets" / "representative-quality-evidence.json"
DOC_SPRITE_VISUAL = ROOT / "docs" / "assets" / "sprite-before-after.svg"


class QualityFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.fixtures = {item["type"]: item for item in cls.payload["fixtures"]}

    def test_all_representative_fixture_types_are_present(self) -> None:
        self.assertEqual(
            set(self.fixtures),
            {"sprite", "mesh-3d", "rig-animation", "audio", "scene", "visual-regression", "gameplay"},
        )

    def test_fixtures_are_synthetic_rights_cleared_and_human_approved(self) -> None:
        self.assertEqual(self.payload["fixture_policy"], "synthetic-rights-cleared-no-external-tools")
        for fixture in self.fixtures.values():
            self.assertEqual(fixture["rights"]["license"], "CC0-1.0")
            self.assertFalse(fixture["rights"]["identity_or_voice"])
            self.assertEqual(fixture["human_approval"]["status"], "approved-for-fixture")
            self.assertEqual(fixture["overall"], "pass")

    def test_every_check_has_threshold_and_pass_status(self) -> None:
        for fixture in self.fixtures.values():
            self.assertGreater(len(fixture["checks"]), 2)
            for check in fixture["checks"]:
                self.assertIn("threshold", check)
                self.assertIn("before", check)
                self.assertIn("after", check)
                self.assertEqual(check["status"], "pass")

    def test_sprite_candidate_improves_alignment_without_pixel_changes(self) -> None:
        checks = {check["id"]: check for check in self.fixtures["sprite"]["checks"]}
        self.assertEqual((checks["baseline-variance-px"]["before"], checks["baseline-variance-px"]["after"]), (3, 0))
        self.assertEqual((checks["loop-seam-px"]["before"], checks["loop-seam-px"]["after"]), (4, 0))
        self.assertEqual(checks["pixel-content-changes"]["after"], 0)

    def test_specific_domain_gates_are_represented(self) -> None:
        required = {
            "mesh-3d": {"non-manifold-edges", "invalid-normals", "uv-overlap-percent", "lod-count", "collision-present"},
            "rig-animation": {"unweighted-vertices", "max-foot-slide-cm", "loop-position-error-m", "root-motion-discontinuities"},
            "audio": {"true-peak-dbtp", "integrated-loudness-lufs", "loop-seam-dbfs", "clipped-samples"},
            "scene": {"spawn-goal-reachability-percent", "navigation-islands", "p95-frame-time-ms", "peak-memory-mb", "draw-calls"},
            "visual-regression": {"different-pixels-percent", "ssim", "unmasked-camera-drift-px"},
            "gameplay": {"launch-success", "core-action-success", "win-loss-feedback", "restart-success", "crashes"},
        }
        for fixture_type, expected in required.items():
            actual = {check["id"] for check in self.fixtures[fixture_type]["checks"]}
            self.assertTrue(expected.issubset(actual), f"{fixture_type}: {sorted(expected - actual)}")

    def test_sprite_visual_is_valid_accessible_svg(self) -> None:
        root = ET.parse(SPRITE_VISUAL).getroot()
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        self.assertEqual(root.attrib["width"], "1400")
        self.assertEqual(root.attrib["height"], "800")
        self.assertIsNotNone(root.find("svg:title", namespace))
        self.assertIsNotNone(root.find("svg:desc", namespace))

    def test_pages_examples_match_test_evidence(self) -> None:
        self.assertEqual(DOC_EVIDENCE.read_bytes(), EVIDENCE.read_bytes())
        self.assertEqual(DOC_SPRITE_VISUAL.read_bytes(), SPRITE_VISUAL.read_bytes())


if __name__ == "__main__":
    unittest.main()
