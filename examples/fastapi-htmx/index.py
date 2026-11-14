"""Build a page that requests quotes with htmx."""

from htmlkit import Element, body, button, div, h1, head, html, link, meta, p, script, title


def index_page() -> Element:
    """Create the index page with a button and a quote container."""
    return html(
        head(
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("Quotes with htmx"),
            link(rel="stylesheet", href="/styles.css"),
            script(
                src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.11/dist/htmx.min.js",
                integrity="sha384-2OatzQy1H+Zd/IIrjr1TcuDGqLXeHhbooAyJY1KdQMKnr4LZ22k31GBLdYKHmVjg",
                crossorigin="anonymous",
                defer=True,
            ),
        ),
        body(
            h1("Quotes with htmx"),
            p("Click the button to load a random quote without reloading the page."),
            button(
                "Get a quote",
                type="button",
                hx_get="/quotes",
                hx_target="#quote",
                hx_swap="innerHTML",
            ),
            div(
                p("Your quote will appear here."),
                id="quote",
                aria_live="polite",
            ),
        ),
        lang="en",
    )
