"""Compare htmlkit list construction with rendering a compiled Jinja template."""

from statistics import median
from timeit import repeat

from jinja2 import Environment

from htmlkit import li, ul

ITEM_COUNT = 1_000
CONTEXT = {"items": [f"Item {index} & <content>" for index in range(ITEM_COUNT)]}
TEMPLATE = Environment(autoescape=True).from_string(
    "<ul>{% for item in items %}<li>{{ item }}</li>{% endfor %}</ul>"
)
NUMBER = 1_000
REPEAT = 5


def render_htmlkit() -> str:
    """Render an unordered list with individually constructed list items."""
    return str(ul([li(item) for item in CONTEXT["items"]]))


def render_htmlkit_repeat() -> str:
    """Render an unordered list by repeating the list item element."""
    return str(ul(li.repeat(CONTEXT["items"])))


def render_jinja() -> str:
    """Render an unordered list using the compiled Jinja template."""
    return TEMPLATE.render(CONTEXT)


def main() -> None:
    """Validate list output and report median rendering times."""
    expected = (
        "<ul>"
        + "".join(f"<li>Item {index} &amp; &lt;content&gt;</li>" for index in range(ITEM_COUNT))
        + "</ul>"
    )
    assert render_htmlkit() == render_htmlkit_repeat() == render_jinja() == expected

    print(f"{REPEAT} repeats of {NUMBER:,} lists with {ITEM_COUNT:,} items; median time per list")
    print("Input preparation and Jinja compilation excluded; autoescaping enabled.")
    for name, render in (
        ("htmlkit", render_htmlkit),
        ("htmlkit repeat", render_htmlkit_repeat),
        ("Jinja", render_jinja),
    ):
        seconds = median(repeat(render, number=NUMBER, repeat=REPEAT)) / NUMBER
        print(f"{name:12}: {seconds * 1_000_000:9.2f} µs/list")


if __name__ == "__main__":
    main()
