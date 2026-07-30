#!/usr/bin/env python3
"""Build a dependency-free static documentation site for GitHub Pages."""

from __future__ import annotations

import argparse
import html
from pathlib import Path
import re
import shutil


LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
INLINE_CODE = re.compile(r"`([^`]+)`")


def inline(value: str) -> str:
    escaped = html.escape(value, quote=True)
    escaped = INLINE_CODE.sub(lambda match: f"<code>{match.group(1)}</code>", escaped)

    def link(match: re.Match[str]) -> str:
        label, target = match.groups()
        decoded = html.unescape(target)
        if decoded.startswith(("https://", "http://", "#", "/")) or not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", decoded):
            href = html.escape(decoded, quote=True)
            return f'<a href="{href}">{label}</a>'
        return label

    return LINK.sub(link, escaped)


def markdown_to_html(source: str) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code: list[str] = []
    list_kind: str | None = None

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            output.append(f"</{list_kind}>")
            list_kind = None

    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                output.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            title = heading.group(2).strip(" #")
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            output.append(f'<h{level} id="{slug}">{inline(title)}</h{level}>')
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        ordered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if bullet or ordered:
            flush_paragraph()
            kind = "ul" if bullet else "ol"
            if list_kind != kind:
                close_list()
                output.append(f"<{kind}>")
                list_kind = kind
            output.append(f"<li>{inline((bullet or ordered).group(1))}</li>")
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            close_list()
            output.append(f"<blockquote>{inline(stripped.lstrip('> '))}</blockquote>")
            continue
        if not stripped:
            flush_paragraph()
            close_list()
            continue
        paragraph.append(stripped)
    if in_code:
        output.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
    flush_paragraph()
    close_list()
    return "\n".join(output)


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Codex AI Game Studio documentation">
  <title>{html.escape(title)} · Codex AI Game Studio</title>
  <link rel="stylesheet" href="/codex-ai-game-studio/assets/site.css">
</head>
<body>
  <header><a class="brand" href="/codex-ai-game-studio/">Codex AI Game Studio</a>
    <nav aria-label="Primary"><a href="/codex-ai-game-studio/tutorials/">Tutorials</a><a href="/codex-ai-game-studio/validation/">Validation</a><a href="/codex-ai-game-studio/privacy/">Privacy</a><a href="/codex-ai-game-studio/support/">Support</a></nav>
  </header>
  <main>{body}</main>
  <footer>MIT licensed · No hosted backend in the core plugin · <a href="https://github.com/frabcd/codex-ai-game-studio">GitHub</a></footer>
</body>
</html>
"""


def title_from(source: str, fallback: str) -> str:
    for line in source.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def write_page(output: Path, route: str, source_path: Path) -> None:
    source = source_path.read_text(encoding="utf-8")
    target = output / route / "index.html" if route else output / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page(title_from(source, source_path.stem), markdown_to_html(source)), encoding="utf-8", newline="\n")


def build(root: Path, output: Path) -> list[Path]:
    root = root.resolve()
    output = output.resolve()
    def choose(*paths: str) -> Path:
        candidates = [root / value for value in paths]
        return next((path for path in candidates if path.is_file()), candidates[0])

    required = {
        "": root / "README.md",
        "tutorials": root / "docs" / "TUTORIALS.md",
        "validation": root / "docs" / "VALIDATION.md",
        "privacy": choose("docs/PRIVACY.md", "docs/privacy/index.md"),
        "terms": choose("docs/TERMS.md", "docs/terms/index.md"),
        "support": choose("SUPPORT.md", "docs/support/index.md"),
        "security": root / "SECURITY.md",
        "contributing": root / "CONTRIBUTING.md",
    }
    missing = [str(path.relative_to(root)) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("required Pages sources are missing: " + ", ".join(missing))
    if output == root or output in root.parents:
        raise ValueError("output must not contain or replace the repository root")
    output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for route, source in required.items():
        write_page(output, route, source)
        written.append(output / route / "index.html" if route else output / "index.html")

    docs_root = root / "docs"
    routed_sources = {path.resolve() for path in required.values()}
    for source in sorted(docs_root.rglob("*.md")):
        if source.resolve() in routed_sources:
            continue
        route = (Path("docs") / source.relative_to(docs_root).with_suffix("")).as_posix().lower()
        write_page(output, route, source)
        written.append(output / route / "index.html")

    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    css = """:root{color-scheme:dark;--bg:#07111d;--panel:#0e2132;--text:#eaf7ff;--muted:#9fc2d8;--accent:#08c7f7;--accent2:#8a65ff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 0,#123754,var(--bg) 35rem);color:var(--text);font:16px/1.65 system-ui,sans-serif}header,main,footer{max-width:1080px;margin:auto;padding:1.25rem}header{display:flex;gap:1rem;align-items:center;justify-content:space-between}.brand{font-weight:800;color:var(--text);text-decoration:none}nav{display:flex;gap:1rem;flex-wrap:wrap}a{color:var(--accent)}main{background:color-mix(in srgb,var(--panel) 86%,transparent);border:1px solid #24455d;border-radius:18px;margin-top:1rem;padding:clamp(1.2rem,4vw,3rem);box-shadow:0 24px 80px #0008}h1,h2,h3{line-height:1.2}h1{font-size:clamp(2rem,6vw,4.2rem);background:linear-gradient(90deg,var(--accent),var(--accent2));color:transparent;background-clip:text}pre{overflow:auto;padding:1rem;border-radius:10px;background:#02070d;border:1px solid #24455d}code{font-family:ui-monospace,monospace}blockquote{border-left:4px solid var(--accent2);margin-left:0;padding-left:1rem;color:var(--muted)}footer{color:var(--muted);font-size:.9rem}@media(max-width:700px){header{align-items:flex-start;flex-direction:column}}"""
    (assets / "site.css").write_text(css + "\n", encoding="utf-8", newline="\n")
    written.append(assets / "site.css")
    source_assets = docs_root / "assets"
    if source_assets.is_dir():
        for source in source_assets.rglob("*"):
            if source.is_file():
                relative = source.relative_to(source_assets)
                target = assets / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                written.append(target)
    (output / ".nojekyll").write_text("", encoding="utf-8")
    written.append(output / ".nojekyll")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("_site"))
    args = parser.parse_args()
    written = build(args.root, args.output)
    print(f"Built {len(written)} Pages files in {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
