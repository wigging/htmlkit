"""Build the two-page Bootstrap example with `uv run examples/bootstrap-site/build.py`."""

from pathlib import Path

from htmlkit import (
    Element,
    Fragment,
    a,
    aside,
    body,
    code,
    div,
    h1,
    h2,
    head,
    html,
    link,
    main,
    meta,
    nav,
    p,
    pre,
    title,
)


def nav_link(label: str, href: str, current: str) -> Element:
    """Mark the link when it points to the current page."""
    active = href == current
    return a(
        label,
        href=href,
        class_="nav-link justify-content-start" + (" active" if active else ""),
        aria_current="page" if active else None,
    )


def base_template(filename: str, heading: str, content: Fragment) -> Element:
    """Wrap the page content in the shared Bootstrap layout."""
    return html(
        head(
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title(f"{heading} · htmlkit"),
            link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/bootstrap@6.0.0-alpha.1/dist/css/bootstrap.min.css",
                integrity="sha384-B/GM4XqrwHnWXNOWMbloTmrYXZg10cakYGmpfsR/bbzQ6JAJI4ihuyADKLnBgrCe",
                crossorigin="anonymous",
            ),
        ),
        body(
            nav(
                div(
                    a("htmlkit", href="index.html", class_="navbar-brand fw-semibold"),
                    div(
                        a("GitHub", href="https://github.com/wigging/htmlkit", class_="nav-link"),
                        class_="nav",
                    ),
                    class_="container",
                ),
                class_="navbar bg-1 border-bottom",
                aria_label="Primary",
            ),
            div(
                div(
                    aside(
                        p("Pages", class_="fs-sm fw-semibold mb-2"),
                        nav(
                            nav_link("Home", "index.html", filename),
                            nav_link("About", "about.html", filename),
                            class_="nav md:flex-column theme-primary",
                            aria_label="Pages",
                        ),
                        class_="col-12 md:col-3",
                    ),
                    main(h1(heading), content, class_="col-12 md:col-9"),
                    class_="row gy-6 md:gx-8",
                ),
                class_="container py-6 md:py-8",
            ),
        ),
        lang="en",
    )


def build_home() -> Fragment:
    """Return the content for the Home page."""
    return Fragment(
        p("A two-page site written in Python with htmlkit and styled with Bootstrap 6."),
        h2("Build it locally", class_="h4 mt-6"),
        p("Run this command from the repository root:"),
        pre(
            code("uv run examples/bootstrap-site/build.py"),
            class_="bg-1 border rounded p-3 text-wrap",
        ),
    )


def build_about() -> Fragment:
    """Return the content for the About page."""
    return Fragment(
        p(
            code("build.py"),
            " writes both pages from the same layout. You can open either HTML "
            "file in a browser without running a web server.",
        ),
        p(a("Read the htmlkit documentation", href="https://gavinw.me/htmlkit/")),
    )


if __name__ == "__main__":
    content = build_home()
    path = Path(__file__).with_name("index.html")
    page = base_template(path.name, "Home", content)
    path.write_text(str(page), encoding="utf-8")

    content = build_about()
    path = Path(__file__).with_name("about.html")
    page = base_template(path.name, "About", content)
    path.write_text(str(page), encoding="utf-8")
