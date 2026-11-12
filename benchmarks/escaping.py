"""Compare short and long text escaping in htmlkit with a compiled Jinja template."""

from functools import partial
from statistics import median
from timeit import repeat

from jinja2 import Environment

from htmlkit import article, h1, p

PARAGRAPH_COUNT = 50
PARAGRAPH_LENGTHS = (16, 63, 64, 65, 256, 600)
TEXTS = {
    "ASCII, no specials": "The quick brown fox jumps over the lazy dog. ",
    "Unicode, no specials": "Café crème — 雪 et 雨. ",
    "Prose, occasional &": "Smith & Sons sell fish and chips on the square every Saturday. ",
    "ASCII with & < >": "Fish & chips <are> tasty, 1 < 2 & 3 > 2. ",
    "Non-ASCII with & < >": "Café & crème <brûlée> — 雪 & 雨. ",
    "All five specials": "&<>\"' café 雪. ",
}
TITLE = "Escaping & <markup>"
TEMPLATE = Environment(autoescape=True).from_string(
    "<article><h1>{{ title }}</h1>{% for text in paragraphs %}<p>{{ text }}</p>{% endfor %}"
    "</article>"
)
NUMBER = 1_000
REPEAT = 5


def paragraphs(phrase: str, length: int) -> list[str]:
    """Return paragraphs of exactly length characters, including whitespace."""
    text = (phrase * (length // len(phrase) + 1))[:length]
    return [text for _ in range(PARAGRAPH_COUNT)]


def render_htmlkit(texts: list[str]) -> str:
    """Render the article with individually constructed paragraphs."""
    return str(article(h1(TITLE), [p(text) for text in texts]))


def render_htmlkit_repeat(texts: list[str]) -> str:
    """Render the article by repeating the paragraph element."""
    return str(article(h1(TITLE), p.repeat(texts)))


def render_jinja(texts: list[str]) -> str:
    """Render the article using the compiled Jinja template."""
    return TEMPLATE.render(title=TITLE, paragraphs=texts)


def main() -> None:
    """Validate escaped output and report median rendering times per text variant."""
    variants = {
        (name, length): paragraphs(phrase, length)
        for length in PARAGRAPH_LENGTHS
        for name, phrase in TEXTS.items()
    }

    # Check the rendered HTML to make sure htmlkit and Jinja create the same output
    for (_, length), texts in variants.items():
        assert len(texts) == PARAGRAPH_COUNT
        assert all(len(text) == length for text in texts)
        escaped = [
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&#34;")
            .replace("'", "&#39;")
            for text in texts
        ]

        expected = (
            "<article><h1>Escaping &amp; &lt;markup&gt;</h1>"
            + "".join(f"<p>{text}</p>" for text in escaped)
            + "</article>"
        )

        assert (
            render_htmlkit(texts) == render_htmlkit_repeat(texts) == render_jinja(texts) == expected
        )

    print(
        f"{REPEAT} repeats of {NUMBER:,} articles with {PARAGRAPH_COUNT} paragraphs; "
        "median time per article"
    )

    print("Input preparation and Jinja compilation excluded; autoescaping enabled.")

    renderers = (
        ("htmlkit", render_htmlkit),
        ("htmlkit repeat", render_htmlkit_repeat),
        ("Jinja", render_jinja),
    )

    print(
        f"\n{'Text':22}{'Chars':>7}{'Output':>10}" + "".join(f"{name:>16}" for name, _ in renderers)
    )

    for (name, length), texts in variants.items():
        size = len(render_jinja(texts).encode())
        timings = []

        for _, render in renderers:
            seconds = median(repeat(partial(render, texts), number=NUMBER, repeat=REPEAT)) / NUMBER
            timings.append(seconds * 1_000_000)

        print(
            f"{name:22}{length:7}{size / 1_000:8.1f} KB"
            + "".join(f"{timing:13.2f} µs" for timing in timings)
        )


if __name__ == "__main__":
    main()
