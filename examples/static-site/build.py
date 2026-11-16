"""Generate a static website with htmlkit.

Uses a base template to build an index page and another page. Run with the
following commands:
  cd examples/static-site
  uv run build.py
"""

from pathlib import Path

from htmlkit import (
    Element,
    Fragment,
    Raw,
    a,
    body,
    code,
    h1,
    h2,
    head,
    html,
    link,
    main,
    meta,
    p,
    pre,
    script,
    strong,
    title,
)

CODE_SNIPPET = """\
from htmlkit import body, h1, head, html, p, title

page = html(
    head(title("Hello from Python")),
    body(
        h1("Hello from Python"),
        p("Built with htmlkit."),
    ),
    lang="en",
)

print(page)"""


def base_template(content: Fragment) -> Element:
    """Base template used by pages."""
    page = html(
        head(
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("Example"),
            link(rel="stylesheet", href="style.css"),
            link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.12.0/styles/atom-one-dark.min.css",
            ),
            script(
                src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.12.0/highlight.min.js"
            ),
        ),
        body(
            main(content),
            script(Raw("hljs.highlightAll();")),
        ),
        lang="en",
    )

    return page


def build_index() -> None:
    """Build the index page."""
    content = Fragment(
        h1("htmlkit"),
        p("Write HTML in Python."),
        p(
            "Build HTML pages with Python objects instead of templates. "
            "Use htmlkit for static websites or HTML responses in web apps."
        ),
        p("View ", a("htmlkit", href="https://github.com/wigging/htmlkit"), " on Github."),
        p("Go to ", a("another page", href="page.html"), " in this example."),
        h2("Installation"),
        p("Requires Python 3.14 or newer."),
        pre(code("uv add htmlkit", class_="language-bash")),
        h2("Example"),
        pre(code(CODE_SNIPPET, class_="language-python")),
    )

    page = base_template(content)

    Path(__file__).with_name("index.html").write_text(str(page), encoding="utf-8")


def build_page() -> None:
    """Build another page that is linked to from the index page."""
    content = Fragment(
        h1("Another Page"),
        p("Hello from yet another page and another pargraph of content."),
        p(strong("Done!")),
        p(a("Go Back", href="index.html")),
    )

    page = base_template(content)

    Path(__file__).with_name("page.html").write_text(str(page), encoding="utf-8")


if __name__ == "__main__":
    build_index()
    build_page()
