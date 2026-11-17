"""HTML document layout, metadata, navigation, and other site-wide elements."""

from htmlkit import (
    Element,
    Fragment,
    Raw,
    a,
    aside,
    body,
    div,
    h6,
    head,
    html,
    link,
    main,
    meta,
    nav,
    script,
    style,
    title,
)


def base_template(content: Fragment) -> Element:
    """Build the base template used for HTML pages."""
    page = html(
        head(
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("htmlkit"),
            link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/bootstrap@6.0.0-alpha.1/dist/css/bootstrap.min.css",
                integrity="sha384-B/GM4XqrwHnWXNOWMbloTmrYXZg10cakYGmpfsR/bbzQ6JAJI4ihuyADKLnBgrCe",
                crossorigin="anonymous",
            ),
            link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.12.0/styles/atom-one-dark.min.css",
            ),
            style(Raw("pre code { border-radius: 0.5rem; }")),
            script(
                src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.12.0/highlight.min.js"
            ),
        ),
        body(
            div(
                div(
                    aside(
                        h6(
                            "Navigation",
                            class_="ps-4 pb-4 fg-secondary border-bottom",
                        ),
                        nav(
                            a(
                                "Overview",
                                href="index.html",
                                class_="nav-link justify-content-start text-wrap",
                            ),
                            a(
                                "Elements and content",
                                href="elements.html",
                                class_="nav-link justify-content-start text-wrap",
                            ),
                            class_="nav flex-column",
                            aria_label="Navigation",
                        ),
                        class_="col-12 md:col-3 md:sticky-top align-self-start",
                    ),
                    main(content, class_="col-12 md:col-9"),
                    class_="row gy-7",
                ),
                class_="container py-7",
            ),
            script(Raw("hljs.highlightAll();")),
        ),
        lang="en",
    )

    return page
