"""HTML document layout, metadata, navigation, and other site-wide elements."""

from importlib.metadata import version

from htmlkit import (
    Element,
    Fragment,
    Raw,
    a,
    aside,
    body,
    div,
    footer,
    h4,
    head,
    html,
    i,
    img,
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
                href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.2/font/bootstrap-icons.min.css",
                integrity="sha384-nWN3KqaaVcbEsCjLSV+2jMjh62Iny/+mN3srM8TZeM8N6aj7eDl5wwYggjAJ4/sJ",
                crossorigin="anonymous",
            ),
            link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.12.0/styles/atom-one-dark.min.css",
            ),
            style(
                Raw(
                    "pre { --bs-code-font-size: var(--bs-font-size-sm); } "
                    "pre code { border-radius: 0.5rem; }"
                )
            ),
            script(
                src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.12.0/highlight.min.js"
            ),
        ),
        body(
            div(
                div(
                    aside(
                        h4(
                            img(
                                src="https://raw.githubusercontent.com/wigging/htmlkit/main/assets/icon.webp",
                                alt="",
                                width=400,
                                height=400,
                                style="width: auto; height: 1.2em",
                            ),
                            "htmlkit",
                            class_="d-flex align-items-center gap-3 ps-4 pb-4 border-bottom",
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
                            a(
                                "Lists and fragments",
                                href="lists-and-fragments.html",
                                class_="nav-link justify-content-start text-wrap",
                            ),
                            a(
                                "Trusted HTML",
                                href="trusted-html.html",
                                class_="nav-link justify-content-start text-wrap",
                            ),
                            a(
                                "FastAPI web app",
                                href="fastapi.html",
                                class_="nav-link justify-content-start text-wrap",
                            ),
                            a(
                                i(class_="bi bi-github"),
                                "GitHub",
                                href="https://github.com/wigging/htmlkit",
                                class_="nav-link justify-content-start text-wrap",
                            ),
                            class_="nav flex-column",
                            aria_label="Navigation",
                        ),
                        class_="col-12 md:col-3 md:sticky-top align-self-start",
                    ),
                    main(
                        content,
                        footer(
                            f"htmlkit v{version('htmlkit')}",
                            class_="text-center my-12 fs-sm fg-secondary",
                        ),
                        class_="col-12 md:col-9",
                    ),
                    class_="row gy-7 md:gx-12",
                ),
                class_="container py-7",
            ),
            script(Raw("hljs.highlightAll();")),
        ),
        lang="en",
    )

    return page
