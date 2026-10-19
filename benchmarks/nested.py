"""Compare time and peak Python memory for nested HTML with htmpy and Jinja."""

import tracemalloc
from functools import partial
from statistics import median
from timeit import repeat

from jinja2 import Environment

from htmpy import div, p

DEPTHS = (10, 100, 1_000, 5_000)
PAYLOAD_REPEATS = (1, 256)
TEXT = "Content & <details>."
ESCAPED_TEXT = "Content &amp; &lt;details&gt;."
NUMBER = 100
REPEAT = 5
TEMPLATE = Environment(autoescape=True).from_string(
    "{% for _ in range(depth) %}<div>{% endfor %}"
    "<p>{{ text }}</p>"
    "{% for _ in range(depth) %}</div>{% endfor %}"
)


def render_nested(depth: int, text: str) -> str:
    """Build a fresh paragraph wrapped in depth divs without retaining children."""
    element = p(text)
    for _ in range(depth):
        element = div(element)
    return str(element)


def main() -> None:
    """Validate nested output and report separate time and peak-memory samples."""
    print(f"{REPEAT} repeats of {NUMBER:,} renders; median time per complete render.")
    print(f"Peak memory: median of {REPEAT} separate single renders with tracemalloc.")
    print("Inputs, Jinja compilation, and validation excluded; autoescaping enabled.")
    print("Intermediate htmpy elements are not retained; Jinja uses template loops.")
    print(
        f"{'Renderer':8} {'Text chars':>10} {'Depth':>7} {'Output bytes':>13} "
        f"{'µs/render':>12} {'Peak KiB':>12}"
    )
    for payload_repeats in PAYLOAD_REPEATS:
        text = TEXT * payload_repeats
        for depth in DEPTHS:
            expected = "<div>" * depth + "<p>" + ESCAPED_TEXT * payload_repeats + "</p>"
            expected += "</div>" * depth
            output_bytes = len(expected.encode("utf-8"))
            renderers = (
                ("htmpy", partial(render_nested, depth, text)),
                ("Jinja", partial(TEMPLATE.render, depth=depth, text=text)),
            )
            for _, render in renderers:
                assert render() == expected

            for name, render in renderers:
                seconds = median(repeat(render, number=NUMBER, repeat=REPEAT)) / NUMBER
                peaks = []
                for _ in range(REPEAT):
                    tracemalloc.start()
                    try:
                        rendered = render()
                        _, peak = tracemalloc.get_traced_memory()
                    finally:
                        tracemalloc.stop()
                    assert rendered == expected
                    peaks.append(peak)
                    del rendered

                print(
                    f"{name:8} {len(text):10,} {depth:7,} {output_bytes:13,} "
                    f"{seconds * 1_000_000:12.2f} {median(peaks) / 1024:12.2f}"
                )


if __name__ == "__main__":
    main()
