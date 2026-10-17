"""Compare htmpy page construction with rendering a compiled Jinja template."""

from statistics import median
from timeit import repeat

from jinja2 import Environment

from htmpy import body, h1, head, html, link, meta, p

CONTEXT = {"heading": "Hello & welcome", "message": "Build a simple <HTML> page."}
TEMPLATE = Environment(autoescape=True).from_string(
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<link rel="stylesheet" href="/styles.css"></head><body>'
    '<h1>{{ heading }}</h1><p class="intro">{{ message }}</p></body></html>'
)
PAGE = html({"lang": "en"})
HEAD = head(
    meta({"charset": "utf-8"}),
    link({"rel": "stylesheet", "href": "/styles.css"}),
)
PARAGRAPH = p({"class": "intro"})
NUMBER = 10_000
REPEAT = 5


def render_htmpy_fresh() -> str:
    """Render a page by constructing every htmpy element anew."""
    return str(
        html(
            {"lang": "en"},
            head(
                meta({"charset": "utf-8"}),
                link({"rel": "stylesheet", "href": "/styles.css"}),
            ),
            body(h1(CONTEXT["heading"]), p({"class": "intro"}, CONTEXT["message"])),
        )
    )


def render_htmpy() -> str:
    """Render a page while reusing prepared htmpy elements."""
    return str(PAGE(HEAD, body(h1(CONTEXT["heading"]), PARAGRAPH(CONTEXT["message"]))))


def render_jinja() -> str:
    """Render a page using the compiled Jinja template."""
    return TEMPLATE.render(CONTEXT)


def main() -> None:
    """Validate page output and report median rendering times."""
    expected = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<link rel="stylesheet" href="/styles.css"></head><body>'
        '<h1>Hello &amp; welcome</h1><p class="intro">'
        "Build a simple &lt;HTML&gt; page.</p></body></html>"
    )
    assert render_htmpy_fresh() == render_htmpy() == render_jinja() == expected

    print(f"{REPEAT} repeats of {NUMBER:,} pages; median time per page")
    print("Static htmpy preparation and Jinja compilation excluded; autoescaping enabled.")
    for name, render in (
        ("htmpy fresh", render_htmpy_fresh),
        ("htmpy reused", render_htmpy),
        ("Jinja", render_jinja),
    ):
        seconds = median(repeat(render, number=NUMBER, repeat=REPEAT)) / NUMBER
        print(f"{name:12}: {seconds * 1_000_000:9.2f} µs/page")


if __name__ == "__main__":
    main()
