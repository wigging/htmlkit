"""HTML document layout, metadata, navigation, and other site-wide elements."""

from htmlkit import Element, Fragment, body, head, html, link, main, meta, title


def base_template(content: Fragment) -> Element:
    """Build the base template used for HTML pages."""
    page = html(
        head(
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("Docs for htmlkit"),
            link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/bootstrap@6.0.0-alpha.1/dist/css/bootstrap.min.css",
                integrity="sha384-B/GM4XqrwHnWXNOWMbloTmrYXZg10cakYGmpfsR/bbzQ6JAJI4ihuyADKLnBgrCe",
                crossorigin="anonymous",
            ),
        ),
        body(
            main(content, class_="container"),
        ),
        lang="en",
    )

    return page
