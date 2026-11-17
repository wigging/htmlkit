"""Build the docs."""

from pathlib import Path

from layout import base_template

from htmlkit import Element, Fragment, h1, p


def build_index() -> Element:
    """Build the index page."""
    content = Fragment(h1("htmlkit"), p("Hello there!"))
    page = base_template(content)
    return page


if __name__ == "__main__":
    page = build_index()
    Path(__file__).with_name("index.html").write_text(str(page), encoding="utf-8")
