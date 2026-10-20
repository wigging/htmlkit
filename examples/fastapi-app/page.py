"""Build a basic HTML web page."""

from htmpy import Element, body, h1, head, html, p, title


def basic_page() -> Element:
    """Create a basic HTML web page."""
    page = html(
        head(title("Hello there!")),
        body(
            h1("Hello there!"),
            p(
                "This is just a basic web page that is used for a FastAPI web app example. "
                "The page is returned as a HTMLResponse object in FastAPI."
            ),
            p("The last paragraph is here."),
        ),
        lang="en",
    )

    return page
