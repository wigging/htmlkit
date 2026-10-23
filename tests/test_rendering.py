"""Check complete documents and nested lists."""

from htmpy import body, h1, head, html, li, link, meta, ol, p, ul


def test_document() -> None:
    """Verify HTML documents include a doctype and nested content."""
    page = html(head(), body(h1("Hello"), p("First"), p("Second")), lang="en")
    assert str(page) == (
        '<!doctype html><html lang="en"><head></head><body>'
        "<h1>Hello</h1><p>First</p><p>Second</p></body></html>"
    )
    assert str(html()) == "<!doctype html><html></html>"


def test_head_metadata() -> None:
    """Verify head metadata renders void tags and escapes attribute values."""
    page = html(
        head(
            meta(charset="utf-8"),
            meta(name="description", content='A & "B"'),
            link(rel="stylesheet", href="/style.css?a=1&b=2"),
        ),
        body(p("Hello")),
    )
    assert str(page) == (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="description" content="A &amp; &#34;B&#34;">'
        '<link rel="stylesheet" href="/style.css?a=1&amp;b=2">'
        "</head><body><p>Hello</p></body></html>"
    )


def test_lists() -> None:
    """Verify nested ordered and unordered lists preserve structure and attributes."""
    element = ul(
        [li("A & B"), li("Steps", ol(li("First"), li("Last", value=7), start=3))],
        class_="items",
    )
    assert str(element) == (
        '<ul class="items"><li>A &amp; B</li><li>Steps<ol start="3">'
        '<li>First</li><li value="7">Last</li></ol></li></ul>'
    )
