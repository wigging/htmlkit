"""Check element construction, escaping, composition, and interoperability."""

from copy import copy, deepcopy
from pickle import dumps, loads
from types import MappingProxyType

import pytest
from fastapi.responses import HTMLResponse
from jinja2 import Environment
from markupsafe import Markup

from htmpy import (
    Child,
    Element,
    Fragment,
    Raw,
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
    script,
    ul,
)


def test_public_construction():
    """Verify direct construction snapshots inputs and supports reuse and copying."""
    attributes = {"title": '"<&'}
    children: list[Child] = ["<unsafe>&", p("<nested>")]
    element = Element("section", MappingProxyType(attributes), children)
    attributes.clear()
    children.clear()
    expected = '<section title="&quot;&lt;&amp;">&lt;unsafe&gt;&amp;<p>&lt;nested&gt;</p></section>'
    assert str(element) == expected
    assert str(Element("p", "<unsafe>&")) == "<p>&lt;unsafe&gt;&amp;</p>"
    assert str(Element("p", (), "<unsafe>&")) == "<p>&lt;unsafe&gt;&amp;</p>"
    assert str(element({"title": None}, "<next>")) == "<section>&lt;next&gt;</section>"
    assert str(element.repeat(["<one>", "&"])) == (
        '<section title="&quot;&lt;&amp;">&lt;one&gt;</section>'
        '<section title="&quot;&lt;&amp;">&amp;</section>'
    )
    for cloned in (copy(element), deepcopy(element), loads(dumps(element))):
        assert str(cloned) == expected
    assert str(Element("html", Element("my-widget"))) == (
        "<!doctype html><html><my-widget></my-widget></html>"
    )


@pytest.mark.parametrize("tag", ["", "P", "p onclick=x", "p><script", "p/", "p\n"])
def test_invalid_tag(tag):
    """Reject empty, uppercase, and unsafe tag names."""
    with pytest.raises(ValueError, match="Invalid HTML tag name"):
        Element(tag)


@pytest.mark.parametrize(
    "attributes, error",
    [({'x="injected"': "value"}, ValueError), ({"title": []}, TypeError)],
)
def test_constructor_attributes(attributes, error):
    """Reject invalid attribute names and unsupported values."""
    with pytest.raises(error):
        Element("p", attributes, "text")


def test_constructor_rejects_raw_keywords():
    """Reject internal constructor keywords and attributes after children."""
    with pytest.raises(TypeError):
        Element(_tag="p", _attributes=(), _content="<script>")  # ty: ignore[no-matching-overload]
    with pytest.raises(TypeError):
        Element("p", "text", {"id": "late"})  # ty: ignore[no-matching-overload]


@pytest.mark.parametrize("tag", ["meta", "link", "img", "br"])
def test_constructor_void(tag):
    """Verify directly constructed void elements reject children and survive copying."""
    element = Element(tag, {"id": "example"})
    assert str(element) == f'<{tag} id="example">'
    for child in ("text", "", None, []):
        with pytest.raises(ValueError, match="cannot have children"):
            Element(tag, child)
    for cloned in (copy(element), deepcopy(element), loads(dumps(element))):
        assert str(cloned) == str(element)


@pytest.mark.parametrize("as_fragment", [False, True])
def test_html_response(as_fragment):
    """Verify FastAPI responses encode elements and fragments with correct headers."""
    page = html(body(p({"title": '"café"'}, "雪 & <hello>")))
    if as_fragment:
        page = Fragment(page)
    response = HTMLResponse(page, status_code=201)
    expected = (
        '<!doctype html><html><body><p title="&quot;café&quot;">'
        "雪 &amp; &lt;hello&gt;</p></body></html>"
    ).encode()
    assert response.body == expected
    assert response.status_code == 201
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-length"] == str(len(expected))


@pytest.mark.parametrize("element", [p("café"), Fragment(p("café"))])
def test_encode(element):
    """Verify encoding choices and error handling for rendered HTML."""
    assert element.encode() == b"<p>caf\xc3\xa9</p>"
    assert element.encode("latin-1") == b"<p>caf\xe9</p>"
    assert element.encode("ascii", errors="xmlcharrefreplace") == b"<p>caf&#233;</p>"
    with pytest.raises(UnicodeEncodeError):
        element.encode("ascii")


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


@pytest.mark.parametrize("element, tag", [(meta, "meta"), (link, "link")])
def test_void_elements(element, tag):
    """Verify void shortcuts support attribute updates but reject all children."""
    assert str(element) == f"<{tag}>"
    assert str(element()) == f"<{tag}>"
    base = element({"id": "original"})
    assert str(base({"id": "updated", "hidden": True, "title": None})) == (
        f'<{tag} id="updated" hidden>'
    )
    assert str(base) == f'<{tag} id="original">'
    assert str(base({"id": None})) == f"<{tag}>"
    for child in ("text", "", None, [], (), 0):
        with pytest.raises(ValueError, match=f"The {tag} element cannot have children"):
            element(child)
    with pytest.raises(ValueError, match=f"The {tag} element cannot have children"):
        element({"id": "example"}, p("child"))


@pytest.mark.parametrize(
    "element, attrs",
    [(p, {"cls": "intro"}), (p, {"content": "Hello"}), (meta, {"charset": "utf-8"})],
)
def test_keyword_arguments_rejected(element, attrs):
    """Reject keyword arguments in element calls."""
    with pytest.raises(TypeError):
        element(**attrs)


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


def test_escaping():
    """Verify text and attribute escaping without double-escaping nested elements."""
    assert str(p("雪 & <tag> \"'")) == "<p>雪 &amp; &lt;tag&gt; \"'</p>"
    child = li("<one> & two")
    assert str(ul([child, str(child)])) == (
        "<ul><li>&lt;one&gt; &amp; two</li>"
        "&lt;li&gt;&amp;lt;one&amp;gt; &amp;amp; two&lt;/li&gt;</ul>"
    )
    assert str(p({"title": "\"<&'"}, "<script>alert('x')</script> &")) == (
        "<p title=\"&quot;&lt;&amp;&#x27;\">&lt;script&gt;alert('x')&lt;/script&gt; &amp;</p>"
    )
    with pytest.raises(ValueError):
        p({'x="injected"': "value"})


def test_attributes():
    """Verify literal attribute names and string, integer, boolean, and null values."""
    assert (
        str(p({"class": "intro", "data-id": 7, "hidden": True, "title": None, "inert": False}))
        == '<p class="intro" data-id="7" hidden></p>'
    )
    assert str(p({"tabindex": 0})) == '<p tabindex="0"></p>'
    assert str(p({"data_id": "literal"})) == '<p data_id="literal"></p>'
    assert str(p({}, "Hello")) == "<p>Hello</p>"


def test_attribute_order():
    """Reject attribute mappings outside the first argument position."""
    with pytest.raises(TypeError):
        p("Hello", {"class": "intro"})  # ty: ignore[no-matching-overload]
    with pytest.raises(TypeError):
        p({"id": "first"}, {"class": "intro"})  # ty: ignore[no-matching-overload]


def test_reuse():
    """Verify element calls replace children and merge attributes without mutation."""
    base = p({"class": "note"}, "Original")
    changed = base({"class": "new", "id": "message"}, "Changed")
    assert str(base) == '<p class="note">Original</p>'
    assert str(changed) == '<p class="new" id="message">Changed</p>'
    assert str(base({"class": None}, "Original")) == "<p>Original</p>"
    assert str(base("Next & <last>")) == '<p class="note">Next &amp; &lt;last&gt;</p>'
    assert str(base()) == '<p class="note"></p>'
    assert str(p) == "<p></p>"


@pytest.mark.parametrize("element", [p({"class": "note"}, "A & <B>"), meta({"charset": "utf-8"})])
def test_element_copy(element):
    """Verify copying and pickling preserve rendering and attribute updates."""
    for cloned in (copy(element), deepcopy(element), loads(dumps(element))):
        assert str(cloned) == str(element)
        assert str(cloned({"id": "updated"})) == str(element({"id": "updated"}))


def test_child_snapshot():
    """Verify later changes to child lists do not alter rendered elements."""
    children: list[Child] = [p("First"), (None, " & ", 0)]
    element = body(children)
    children.clear()
    assert str(element) == "<body><p>First</p> &amp; 0</body>"
    assert str(element) == "<body><p>First</p> &amp; 0</body>"


def test_attribute_snapshot():
    """Verify later changes to attribute mappings do not alter rendered elements."""
    attributes = {"class": "intro"}
    element = body(attributes, "Before ", p("inside"), " after.")
    attributes["class"] = "changed"
    assert str(element) == '<body class="intro">Before <p>inside</p> after.</body>'


def test_fragment():
    """Verify fragments snapshot, escape, nest, and copy children without a wrapper."""
    children: list[Child] = ["<unsafe> & ", p("雪"), (None, 0, ["café"])]
    generated = (child for child in children)
    fragment = Fragment.from_iterable(generated)
    assert list(generated) == []
    children.clear()
    expected = "&lt;unsafe&gt; &amp; <p>雪</p>0café"
    assert str(fragment) == expected
    assert str(Fragment("<unsafe> & ", p("雪"), (None, 0, ["café"]))) == expected
    assert str(Fragment()) == str(Fragment.from_iterable([])) == ""
    assert str(body(Fragment(fragment, "!"))) == f"<body>{expected}!</body>"
    assert str(Fragment("<em>raw</em>")) == "&lt;em&gt;raw&lt;/em&gt;"
    assert str(Fragment(str(p("<&")))) == "&lt;p&gt;&amp;lt;&amp;amp;&lt;/p&gt;"
    for cloned in (copy(fragment), deepcopy(fragment), loads(dumps(fragment))):
        assert isinstance(cloned, Fragment)
        assert str(body(cloned)) == f"<body>{expected}</body>"


@pytest.mark.parametrize("child", [{"id": "not-attributes"}, object()])
def test_fragment_rejects_invalid_children(child):
    """Reject mappings and unsupported objects as fragment children."""
    with pytest.raises(TypeError):
        Fragment(child)
    with pytest.raises(TypeError):
        Fragment.from_iterable([child])


def test_repeat():
    """Verify repeated elements snapshot content and retain the base attributes."""
    row = li({"class": 'a&"b'}, "replaced")
    nested: list[Child] = ["雪 & ", p("<inside>")]
    items: list[Child] = ["<one> \"' &", 0, None, nested]
    fragment = row.repeat(item for item in items)
    assert isinstance(fragment, Fragment)
    items.clear()
    nested.clear()
    expected = (
        '<li class="a&amp;&quot;b">&lt;one&gt; "\' &amp;</li>'
        '<li class="a&amp;&quot;b">0</li>'
        '<li class="a&amp;&quot;b"></li>'
        '<li class="a&amp;&quot;b">雪 &amp; <p>&lt;inside&gt;</p></li>'
    )
    assert str(fragment) == expected
    assert str(ul(fragment)) == f"<ul>{expected}</ul>"
    assert str(body("Before ", [fragment, (fragment,)], " after")) == (
        f"<body>Before {expected}{expected} after</body>"
    )
    assert str(p.repeat([fragment])) == f"<p>{expected}</p>"
    assert str(row) == '<li class="a&amp;&quot;b">replaced</li>'
    assert str(ul(li.repeat([]))) == "<ul></ul>"
    assert str(ul(str(li.repeat(["<unsafe>"])))) == (
        "<ul>&lt;li&gt;&amp;lt;unsafe&amp;gt;&lt;/li&gt;</ul>"
    )
    for cloned in (copy(fragment), deepcopy(fragment), loads(dumps(fragment))):
        assert str(ul(cloned)) == f"<ul>{expected}</ul>"


@pytest.mark.parametrize("items", [[{"id": "not-an-attribute-update"}], [object()]])
def test_repeat_rejects_invalid_content(items):
    """Reject mappings and unsupported objects as repeated content."""
    with pytest.raises(TypeError):
        li.repeat(items)


def test_repeat_rejects_void_elements():
    """Reject repeating void elements even with an empty iterable."""
    for element in (meta, link):
        for items in ([], [None], ["text"]):
            with pytest.raises(ValueError, match="cannot have children"):
                element.repeat(items)


def test_raw():
    """Verify trusted strings bypass escaping and retain that behavior when copied."""
    code = 'if (a < b && c) { go("<x>"); }'
    assert str(script(Raw(code))) == f"<script>{code}</script>"
    assert str(Raw("<em>raw</em>")) == "<em>raw</em>"
    assert str(p(Raw("<b>&</b>"), " & ", [Raw("<i>"), "<"])) == "<p><b>&</b> &amp; <i>&lt;</p>"
    assert str(Fragment(Raw("<hr>"), "<")) == "<hr>&lt;"
    assert str(li.repeat([Raw("<b>x</b>"), "<"])) == "<li><b>x</b></li><li>&lt;</li>"
    assert str(p(str(Raw("<b>")))) == "<p>&lt;b&gt;</p>"
    assert Raw("<br>").encode() == b"<br>"
    for cloned in (copy(Raw("<br>")), deepcopy(Raw("<br>")), loads(dumps(Raw("<br>")))):
        assert isinstance(cloned, Raw)
        assert str(cloned) == "<br>"
    with pytest.raises(TypeError):
        Raw(p("not a string"))  # ty: ignore[invalid-argument-type]


def test_html_protocol():
    """Verify HTML protocol interoperability with custom objects, Markup, and Jinja."""

    class Widget:
        def __html__(self) -> str:
            return "<widget>&</widget>"

    assert str(p(Widget())) == "<p><widget>&</widget></p>"
    assert str(p(Markup("<b>safe</b>"), "<unsafe>")) == "<p><b>safe</b>&lt;unsafe&gt;</p>"
    assert str(Fragment.from_iterable([Widget(), Markup("&amp;")])) == "<widget>&</widget>&amp;"
    assert p("A & B").__html__() == "<p>A &amp; B</p>"
    assert Fragment("<").__html__() == "&lt;"
    template = Environment(autoescape=True).from_string("<div>{{ content }}</div>")
    for content in (p("A & B"), Fragment(p("A & B")), Raw("<p>A &amp; B</p>")):
        assert template.render(content=content) == "<div><p>A &amp; B</p></div>"
    assert template.render(content=str(p("A & B"))) == "<div>&lt;p&gt;A &amp;amp; B&lt;/p&gt;</div>"


def test_equality():
    """Verify equality and hashing distinguish markup types and rendered content."""
    assert p({"id": "x"}, "A") == p({"id": "x"}, "A") == Element("p", {"id": "x"}, "A")
    assert p("A") != p("B") and p("A") != Element("div", "A")
    assert Fragment(p("A")) == Fragment(p("A")) != p("A")
    assert Raw("<p>A</p>") != p("A")
    assert p("A") != "<p>A</p>"
    assert len({p("A"), p("A"), Fragment(p("A")), Raw("<p>A</p>")}) == 3
    assert repr(p("A & B")) == "Element('<p>A &amp; B</p>')"
