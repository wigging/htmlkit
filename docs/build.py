"""Build docs/content/*.md into docs/*.html with `uv run docs/build.py`."""

from pathlib import Path

from layout import base_template
from markdown_it import MarkdownIt

from htmlkit import Fragment, Raw


def build_docs() -> None:
    """Render each Markdown file inside the shared HTML layout."""
    docs_dir = Path(__file__).parent
    markdown = MarkdownIt("commonmark", {"html": False})

    for source in sorted((docs_dir / "content").glob("*.md")):
        content = Fragment(Raw(markdown.render(source.read_text(encoding="utf-8"))))
        destination = docs_dir / source.with_suffix(".html").name
        page = base_template(content, destination.name)
        destination.write_text(str(page), encoding="utf-8")


if __name__ == "__main__":
    build_docs()
