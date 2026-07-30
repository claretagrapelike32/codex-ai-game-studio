from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.build_pages import build, markdown_to_html


ROOT = Path(__file__).resolve().parents[1]


class PagesBuilderTests(unittest.TestCase):
    def test_markdown_renderer_escapes_source_html(self) -> None:
        rendered = markdown_to_html("# Safe\n\n<script>alert(1)</script>\n")
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)

    def test_pages_include_legal_and_support_routes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ags-pages-") as temporary:
            output_root = Path(temporary).resolve()
            written = build(ROOT, output_root)
            relative = {path.relative_to(output_root).as_posix() for path in written}
            for expected in (
                "index.html",
                "privacy/index.html",
                "terms/index.html",
                "support/index.html",
                "tutorials/index.html",
                "validation/index.html",
                "assets/site.css",
                ".nojekyll",
            ):
                self.assertIn(expected, relative)


if __name__ == "__main__":
    unittest.main()
