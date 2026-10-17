"""Compare fragment construction with rendering compiled Jinja templates."""

from statistics import median
from timeit import repeat

from jinja2 import Environment

from htmpy import Fragment, h1, p

CONTEXT = {"heading": "Hello & welcome", "message": "Build a <fragment> with café."}
ITEM_COUNT = 1_000
ITEMS = [f"Paragraph {index} & <content>" for index in range(ITEM_COUNT)]
ENVIRONMENT = Environment(autoescape=True)
SMALL_TEMPLATE = ENVIRONMENT.from_string("<h1>{{ heading }}</h1> — <p>{{ message }}</p>")
LARGE_TEMPLATE = ENVIRONMENT.from_string("{% for item in items %}<p>{{ item }}</p>{% endfor %}")
REPEAT = 5


def render_small_fragment() -> str:
    return str(Fragment(h1(CONTEXT["heading"]), " — ", p(CONTEXT["message"])))


def render_small_iterable() -> str:
    return str(Fragment.from_iterable((h1(CONTEXT["heading"]), " — ", p(CONTEXT["message"]))))


def render_small_jinja() -> str:
    return SMALL_TEMPLATE.render(CONTEXT)


def render_large_fragment() -> str:
    return str(Fragment(*(p(item) for item in ITEMS)))


def render_large_iterable() -> str:
    return str(Fragment.from_iterable(p(item) for item in ITEMS))


def render_large_repeat() -> str:
    return str(p.repeat(ITEMS))


def render_large_jinja() -> str:
    return LARGE_TEMPLATE.render(items=ITEMS)


def main() -> None:
    small_expected = "<h1>Hello &amp; welcome</h1> — <p>Build a &lt;fragment&gt; with café.</p>"
    large_expected = "".join(
        f"<p>Paragraph {index} &amp; &lt;content&gt;</p>" for index in range(ITEM_COUNT)
    )
    assert (
        render_small_fragment() == render_small_iterable() == render_small_jinja() == small_expected
    )
    assert (
        render_large_fragment()
        == render_large_iterable()
        == render_large_repeat()
        == render_large_jinja()
        == large_expected
    )

    print("Input preparation and Jinja compilation excluded; autoescaping enabled.")
    for title, number, renderers in (
        (
            "Small mixed-content fragment",
            10_000,
            (
                ("Fragment", render_small_fragment),
                ("Fragment.from_iterable", render_small_iterable),
                ("Jinja", render_small_jinja),
            ),
        ),
        (
            f"Fragment with {ITEM_COUNT:,} paragraphs",
            1_000,
            (
                ("Fragment", render_large_fragment),
                ("Fragment.from_iterable", render_large_iterable),
                ("p.repeat", render_large_repeat),
                ("Jinja", render_large_jinja),
            ),
        ),
    ):
        print(f"\n{title}: {REPEAT} repeats of {number:,} renders; median time per fragment")
        for name, render in renderers:
            seconds = median(repeat(render, number=number, repeat=REPEAT)) / number
            print(f"{name:22}: {seconds * 1_000_000:9.2f} µs/fragment")


if __name__ == "__main__":
    main()
