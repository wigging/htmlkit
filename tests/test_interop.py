"""Check encoding and the HTML protocol through htmlkit's public API."""

import json

import pytest
from markupsafe import Markup

from htmlkit import Element, Fragment, Raw, button, div, each, p


@pytest.mark.parametrize("element", [p("café"), Fragment(p("café")), Raw("<p>café</p>")])
def test_encode(element: Element | Fragment | Raw) -> None:
    """Verify encoding choices and error handling for rendered HTML."""
    assert element.encode() == b"<p>caf\xc3\xa9</p>"
    assert element.encode("latin-1") == b"<p>caf\xe9</p>"
    assert element.encode("ascii", errors="xmlcharrefreplace") == b"<p>caf&#233;</p>"
    with pytest.raises(UnicodeEncodeError):
        element.encode("ascii")


def test_html_children() -> None:
    """Insert HTML protocol objects without escaping their trusted markup."""

    class _Widget:
        def __html__(self) -> str:
            return "<widget>&</widget>"

    assert str(p(_Widget())) == "<p><widget>&</widget></p>"
    assert str(p(Markup("<b>safe</b>"), "<unsafe>")) == "<p><b>safe</b>&lt;unsafe&gt;</p>"
    assert str(Fragment.from_iterable([_Widget(), Markup("&amp;")])) == "<widget>&</widget>&amp;"


@pytest.mark.parametrize("content", [p("A & B"), Fragment(p("A & B")), Raw("<p>A &amp; B</p>")])
def test_html_protocol(content: Element | Fragment | Raw) -> None:
    """Expose rendered markup as trusted HTML for template consumers."""
    assert content.__html__() == "<p>A &amp; B</p>"


@pytest.mark.parametrize("prefix, rendered", [("hx_", "hx-"), ("data_hx_", "data-hx-")])
@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
def test_htmx_requests(prefix: str, rendered: str, method: str) -> None:
    """Preserve request URLs, selectors, and case-sensitive swap values."""
    control = button(
        "Send",
        **{
            prefix + method: "/items?q=A&B",
            prefix + "target": "#result",
            prefix + "swap": "outerHTML",
        },
    )
    assert str(control) == (
        f'<button {rendered}{method}="/items?q=A&amp;B" '
        f'{rendered}target="#result" {rendered}swap="outerHTML">Send</button>'
    )


@pytest.mark.parametrize("prefix", ["", "data-"])
@pytest.mark.parametrize(
    "keyword, name",
    [
        ("hx_on_click", "hx-on-click"),
        ("hx_on__before_request", "hx-on--before-request"),
        ("hx_on_htmx_before_request", "hx-on-htmx-before-request"),
        ("hx-on:click", "hx-on:click"),
        ("hx-on::before-request", "hx-on::before-request"),
        ("hx-on:htmx:before-request", "hx-on:htmx:before-request"),
    ],
)
def test_htmx_events(prefix: str, keyword: str, name: str) -> None:
    """Render htmx 2 event names and escape scripts in static and bound attributes."""
    code = "if (1 < 2 && event) this.dataset.state = 'ready'"
    escaped = "if (1 &lt; 2 &amp;&amp; event) this.dataset.state = &#39;ready&#39;"
    expected = f'<button {prefix}{name}="{escaped}">Run</button>'
    assert str(button("Run", **{prefix + keyword: code})) == expected
    template = button("Run", **{prefix + keyword: each["handler"]})
    assert str(template.repeat([{"handler": code}, {"handler": None}])) == (
        expected + "<button>Run</button>"
    )


@pytest.mark.parametrize("name", ["hx_vals", "hx_headers", "hx_request", "data_hx_vals"])
def test_htmx_json(name: str) -> None:
    """Keep JSON valid after HTML parsing, including bound values with metacharacters."""
    value = json.dumps({"note": "A&B <tag>", "enabled": False})
    expected = (
        f'<button {name.replace("_", "-")}="'
        '{&#34;note&#34;: &#34;A&amp;B &lt;tag&gt;&#34;, &#34;enabled&#34;: false}">Send</button>'
    )
    assert str(button("Send", **{name: value})) == expected
    assert str(button("Send", **{name: each["value"]}).repeat([{"value": value}])) == expected


def test_htmx_flags() -> None:
    """Distinguish string-valued htmx options from presence-only attributes."""
    container = div(hx_boost="true", hx_push_url="false", hx_disable=True)
    assert str(container) == '<div hx-boost="true" hx-push-url="false" hx-disable></div>'
    assert str(container(hx_boost="false", hx_disable=False)) == (
        '<div hx-boost="false" hx-push-url="false"></div>'
    )
    template = div(hx_boost=each[0], hx_push_url="false", hx_disable=each[1])
    assert str(template.repeat([("true", True), ("false", False), (None, None)])) == (
        '<div hx-boost="true" hx-push-url="false" hx-disable></div>'
        '<div hx-boost="false" hx-push-url="false"></div>'
        '<div hx-push-url="false"></div>'
    )
