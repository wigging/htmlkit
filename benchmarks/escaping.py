"""Compare escaping of long text content in htmpy with a compiled Jinja template."""

from functools import partial
from statistics import median
from timeit import repeat

from jinja2 import Environment

from htmpy import article, h1, p

PARAGRAPH_COUNT = 50
PARAGRAPH_LENGTH = 600
TEXTS = {
    "ASCII, no specials": "The quick brown fox jumps over the lazy dog. ",
    "Prose, occasional &": "Smith & Sons sell fish and chips on the square every Saturday. ",
    "ASCII with & < >": "Fish & chips <are> tasty, 1 < 2 & 3 > 2. ",
    "Non-ASCII with & < >": "Café & crème <brûlée> — 雪 & 雨. ",
}
TITLE = "Escaping & <markup>"
TEMPLATE = Environment(autoescape=True).from_string(
    "<article><h1>{{ title }}</h1>{% for text in paragraphs %}<p>{{ text }}</p>{% endfor %}"
    "</article>"
)
NUMBER = 1_000
REPEAT = 5


def paragraphs(phrase: str) -> list[str]:
    """Return paragraphs built by repeating the phrase to the paragraph length."""
    text = (phrase * (PARAGRAPH_LENGTH // len(phrase) + 1))[:PARAGRAPH_LENGTH].rstrip()
    return [f"{index}: {text}" for index in range(PARAGRAPH_COUNT)]


def render_htmpy(texts: list[str]) -> str:
    """Render the article with individually constructed paragraphs."""
    return str(article(h1(TITLE), [p(text) for text in texts]))


def render_htmpy_repeat(texts: list[str]) -> str:
    """Render the article by repeating the paragraph element."""
    return str(article(h1(TITLE), p.repeat(texts)))


def render_jinja(texts: list[str]) -> str:
    """Render the article using the compiled Jinja template."""
    return TEMPLATE.render(title=TITLE, paragraphs=texts)


def main() -> None:
    """Validate escaped output and report median rendering times per text variant."""
    variants = {name: paragraphs(phrase) for name, phrase in TEXTS.items()}

    # Check the rendered HTML to make sure htmpy and Jinja create the same output
    for texts in variants.values():
        escaped = [
            text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for text in texts
        ]

        expected = (
            "<article><h1>Escaping &amp; &lt;markup&gt;</h1>"
            + "".join(f"<p>{text}</p>" for text in escaped)
            + "</article>"
        )

        assert render_htmpy(texts) == render_htmpy_repeat(texts) == render_jinja(texts) == expected

    print(
        f"{REPEAT} repeats of {NUMBER:,} articles with {PARAGRAPH_COUNT} paragraphs of "
        f"{PARAGRAPH_LENGTH} characters; median time per article"
    )

    print("Input preparation and Jinja compilation excluded; autoescaping enabled.")

    renderers = (
        ("htmpy", render_htmpy),
        ("htmpy repeat", render_htmpy_repeat),
        ("Jinja", render_jinja),
    )

    print(f"\n{'Text':22}{'Output':>10}" + "".join(f"{name:>16}" for name, _ in renderers))

    for name, texts in variants.items():
        size = len(render_jinja(texts).encode())
        timings = []

        for _, render in renderers:
            seconds = median(repeat(partial(render, texts), number=NUMBER, repeat=REPEAT)) / NUMBER
            timings.append(seconds * 1_000_000)

        print(
            f"{name:22}{size / 1_000:8.1f} KB" + "".join(f"{timing:13.2f} µs" for timing in timings)
        )


if __name__ == "__main__":
    main()
