"""Check rendered HTML documents, metadata, headings, containers, and lists."""

import pytest

from htmpy import (
    a,
    aside,
    body,
    button,
    div,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    head,
    html,
    li,
    link,
    main,
    meta,
    ol,
    p,
    ul,
)


def test_document():
    """Verify HTML documents include a doctype and nested content."""
    page = html({"lang": "en"}, head(), body(h1("Hello"), p("First"), p("Second")))
    assert str(page) == (
        '<!doctype html><html lang="en"><head></head><body>'
        "<h1>Hello</h1><p>First</p><p>Second</p></body></html>"
    )
    assert str(html()) == "<!doctype html><html></html>"


def test_head_metadata():
    """Verify head metadata renders void tags and escapes attribute values."""
    page = html(
        head(
            meta({"charset": "utf-8"}),
            meta({"name": "description", "content": 'A & "B"'}),
            link({"rel": "stylesheet", "href": "/style.css?a=1&b=2"}),
        ),
        body(p("Hello")),
    )
    assert str(page) == (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="description" content="A &amp; &quot;B&quot;">'
        '<link rel="stylesheet" href="/style.css?a=1&amp;b=2">'
        "</head><body><p>Hello</p></body></html>"
    )


@pytest.mark.parametrize(
    "element, tag",
    [(head, "head"), (body, "body"), (h1, "h1"), (p, "p"), (ul, "ul"), (ol, "ol"), (li, "li")],
)
def test_empty(element, tag):
    """Verify empty non-void elements include closing tags."""
    assert str(element()) == f"<{tag}></{tag}>"


@pytest.mark.parametrize(
    "element, tag",
    [(h1, "h1"), (h2, "h2"), (h3, "h3"), (h4, "h4"), (h5, "h5"), (h6, "h6")],
)
def test_headings(element, tag):
    """Verify every heading level supports escaped content and attributes."""
    assert str(element()) == f"<{tag}></{tag}>"
    assert str(element("Section & <title>")) == f"<{tag}>Section &amp; &lt;title&gt;</{tag}>"
    assert str(element({"id": "section"}, "Section ", 2)) == (
        f'<{tag} id="section">Section 2</{tag}>'
    )


@pytest.mark.parametrize(
    "element, tag, attrs, rendered_attrs",
    [
        (button, "button", {"type": "button", "disabled": True}, ' type="button" disabled'),
        (a, "a", {"href": "/?a=1&b=2"}, ' href="/?a=1&amp;b=2"'),
        (div, "div", {"class": "panel"}, ' class="panel"'),
        (main, "main", {"id": "content"}, ' id="content"'),
        (aside, "aside", {"aria-label": "Related"}, ' aria-label="Related"'),
    ],
)
def test_controls_and_containers(element, tag, attrs, rendered_attrs):
    """Verify controls and containers render attributes and nested child sequences."""
    assert str(element()) == f"<{tag}></{tag}>"
    assert str(element(attrs, "A & <B>", [" details ", 2])) == (
        f"<{tag}{rendered_attrs}>A &amp; &lt;B&gt; details 2</{tag}>"
    )


def test_lists():
    """Verify nested ordered and unordered lists preserve structure and attributes."""
    element = ul(
        {"class": "items"},
        [li("A & B"), li("Steps", ol({"start": 3}, li("First"), li({"value": 7}, "Last")))],
    )
    assert str(element) == (
        '<ul class="items"><li>A &amp; B</li><li>Steps<ol start="3">'
        '<li>First</li><li value="7">Last</li></ol></li></ul>'
    )
