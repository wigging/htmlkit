"""Compare time and peak Python memory for nested HTML with htmpy and Jinja."""

import tracemalloc
from functools import partial
from statistics import median
from timeit import repeat

from jinja2 import Environment

from htmpy import div, p, section, span

DEPTHS = (10, 32, 100)
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
MIXED_TEMPLATE = Environment(autoescape=True).from_string(
    "{% for level in range(depth - 1, -1, -1) %}"
    "{% if level % 2 %}<section{% else %}<div{% endif %}"
    '{% if attributed %} data-level="{{ level }}"{% endif %}>{% endfor %}'
    "<p>{{ text }}</p>"
    "{% for level in range(depth) %}"
    "{% if siblings %}<span>{{ level }}</span>{% endif %}"
    "{% if level % 2 %}</section>{% else %}</div>{% endif %}{% endfor %}"
)


def render_nested(depth: int, text: str) -> str:
    """Build a fresh paragraph wrapped in depth divs without retaining children."""
    element = p(text)
    for _ in range(depth):
        element = div(element)
    return str(element)


def render_mixed(depth: int, text: str, *, attributed: bool, siblings: bool) -> str:
    """Alternate wrapper tags, optionally adding attributes or trailing siblings."""
    element = p(text)
    for level in range(depth):
        wrapper = section if level % 2 else div
        if attributed:
            element = wrapper(element, data_level=level)
        elif siblings:
            element = wrapper(element, span(level))
        else:
            element = wrapper(element)
    return str(element)


def main() -> None:
    """Validate nested output and report separate time and peak-memory samples."""
    print(f"{REPEAT} repeats of {NUMBER:,} renders; median time per complete render.")
    print(f"Peak memory: median of {REPEAT} separate single renders with tracemalloc.")
    print("Inputs, Jinja compilation, and validation excluded; autoescaping enabled.")
    print("Intermediate htmpy elements are not retained; Jinja uses template loops.")
    print(f"{'':32} | {'htmpy':^25} | {'Jinja':^25}")
    print(
        f"{'Text chars':>10} {'Depth':>7} {'Output bytes':>13} | "
        f"{'µs/render':>12} {'Peak KiB':>12} | "
        f"{'µs/render':>12} {'Peak KiB':>12}"
    )
    for variant in ("Identical tags", "Mixed tags", "Mixed with attributes", "Mixed with siblings"):
        print(f"\n{variant}")
        _measure(variant)


def _measure(variant: str) -> None:
    """Validate and measure each depth and payload for one nesting shape."""
    mixed = variant != "Identical tags"
    attributed = variant == "Mixed with attributes"
    siblings = variant == "Mixed with siblings"
    for payload_repeats in PAYLOAD_REPEATS:
        text = TEXT * payload_repeats
        for depth in DEPTHS:
            openings = []
            endings = []
            for level in range(depth):
                tag = "section" if mixed and level % 2 else "div"
                attribute = f' data-level="{level}"' if attributed else ""
                openings.append(f"<{tag}{attribute}>")
                sibling = f"<span>{level}</span>" if siblings else ""
                endings.append(f"{sibling}</{tag}>")
            expected = "".join(reversed(openings)) + "<p>" + ESCAPED_TEXT * payload_repeats
            expected += "</p>" + "".join(endings)
            output_bytes = len(expected.encode("utf-8"))
            renderers = (
                (
                    "htmpy",
                    partial(render_mixed, depth, text, attributed=attributed, siblings=siblings)
                    if mixed
                    else partial(render_nested, depth, text),
                ),
                (
                    "Jinja",
                    partial(
                        MIXED_TEMPLATE.render,
                        depth=depth,
                        text=text,
                        attributed=attributed,
                        siblings=siblings,
                    )
                    if mixed
                    else partial(TEMPLATE.render, depth=depth, text=text),
                ),
            )
            for _, render in renderers:
                assert render() == expected

            results = []
            for _, render in renderers:
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

                results.append(f"{seconds * 1_000_000:12.2f} {median(peaks) / 1024:12.2f}")

            print(f"{len(text):10,} {depth:7,} {output_bytes:13,} | " + " | ".join(results))


if __name__ == "__main__":
    main()
