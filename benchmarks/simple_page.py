"""Compare htmpy page construction with rendering a compiled Jinja template."""

from statistics import median
from timeit import repeat

from jinja2 import Environment

from htmpy import body, h1, head, html, p

CONTEXT = {"heading": "Hello & welcome", "message": "Build a simple <HTML> page."}
TEMPLATE = Environment(autoescape=True).from_string(
    '<!doctype html><html lang="en"><head></head><body>'
    '<h1>{{ heading }}</h1><p class="intro">{{ message }}</p></body></html>'
)
NUMBER = 10_000
REPEAT = 5


def render_htmpy() -> str:
    return str(
        html(
            {"lang": "en"},
            head(),
            body(h1(CONTEXT["heading"]), p({"class": "intro"}, CONTEXT["message"])),
        )
    )


def render_jinja() -> str:
    return TEMPLATE.render(CONTEXT)


def main() -> None:
    expected = (
        '<!doctype html><html lang="en"><head></head><body>'
        '<h1>Hello &amp; welcome</h1><p class="intro">'
        'Build a simple &lt;HTML&gt; page.</p></body></html>'
    )
    assert render_htmpy() == render_jinja() == expected

    print(f"{REPEAT} repeats of {NUMBER:,} pages; median time per page")
    print("Jinja template compilation excluded; autoescaping enabled.")
    for name, render in (("htmpy", render_htmpy), ("Jinja", render_jinja)):
        seconds = median(repeat(render, number=NUMBER, repeat=REPEAT)) / NUMBER
        print(f"{name:6}: {seconds * 1_000_000:9.2f} µs/page")


if __name__ == "__main__":
    main()
