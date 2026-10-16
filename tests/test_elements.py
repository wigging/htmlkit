from copy import copy, deepcopy
from pickle import dumps, loads

import pytest
from fastapi.responses import HTMLResponse

from htmpy import (
    Child,
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


def test_html_response():
    page = html(body(p({"title": '"café"'}, "雪 & <hello>")))
    response = HTMLResponse(page, status_code=201)
    expected = (
        '<!doctype html><html><body><p title="&quot;café&quot;">'
        "雪 &amp; &lt;hello&gt;</p></body></html>"
    ).encode()
    assert response.body == expected
    assert response.status_code == 201
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-length"] == str(len(expected))


def test_encode():
    element = p("café")
    assert element.encode() == b"<p>caf\xc3\xa9</p>"
    assert element.encode("latin-1") == b"<p>caf\xe9</p>"
    assert element.encode("ascii", errors="xmlcharrefreplace") == b"<p>caf&#233;</p>"
    with pytest.raises(UnicodeEncodeError):
        element.encode("ascii")


def test_document():
    page = html({"lang": "en"}, head(), body(h1("Hello"), p("First"), p("Second")))
    assert str(page) == (
        '<!doctype html><html lang="en"><head></head><body>'
        "<h1>Hello</h1><p>First</p><p>Second</p></body></html>"
    )
    assert str(html()) == "<!doctype html><html></html>"


def test_head_metadata():
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
    with pytest.raises(TypeError):
        element(**attrs)


@pytest.mark.parametrize(
    "element, tag",
    [(head, "head"), (body, "body"), (h1, "h1"), (p, "p"), (ul, "ul"), (ol, "ol"), (li, "li")],
)
def test_empty(element, tag):
    assert str(element()) == f"<{tag}></{tag}>"


@pytest.mark.parametrize(
    "element, tag",
    [(h1, "h1"), (h2, "h2"), (h3, "h3"), (h4, "h4"), (h5, "h5"), (h6, "h6")],
)
def test_headings(element, tag):
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
    assert str(element()) == f"<{tag}></{tag}>"
    assert str(element(attrs, "A & <B>", [" details ", 2])) == (
        f"<{tag}{rendered_attrs}>A &amp; &lt;B&gt; details 2</{tag}>"
    )


def test_lists():
    element = ul(
        {"class": "items"},
        [li("A & B"), li("Steps", ol({"start": 3}, li("First"), li({"value": 7}, "Last")))],
    )
    assert str(element) == (
        '<ul class="items"><li>A &amp; B</li><li>Steps<ol start="3">'
        '<li>First</li><li value="7">Last</li></ol></li></ul>'
    )


def test_escaping():
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
    assert (
        str(p({"class": "intro", "data-id": 7, "hidden": True, "title": None, "inert": False}))
        == '<p class="intro" data-id="7" hidden></p>'
    )
    assert str(p({"tabindex": 0})) == '<p tabindex="0"></p>'
    assert str(p({"data_id": "literal"})) == '<p data_id="literal"></p>'
    assert str(p({}, "Hello")) == "<p>Hello</p>"


def test_attribute_order():
    with pytest.raises(TypeError):
        p("Hello", {"class": "intro"})
    with pytest.raises(TypeError):
        p({"id": "first"}, {"class": "intro"})


def test_reuse():
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
    for cloned in (copy(element), deepcopy(element), loads(dumps(element))):
        assert str(cloned) == str(element)
        assert str(cloned({"id": "updated"})) == str(element({"id": "updated"}))


def test_child_snapshot():
    children: list[Child] = [p("First"), (None, " & ", 0)]
    element = body(children)
    children.clear()
    assert str(element) == "<body><p>First</p> &amp; 0</body>"
    assert str(element) == "<body><p>First</p> &amp; 0</body>"


def test_attribute_snapshot():
    attributes = {"class": "intro"}
    element = body(attributes, "Before ", p("inside"), " after.")
    attributes["class"] = "changed"
    assert str(element) == '<body class="intro">Before <p>inside</p> after.</body>'


def test_repeat():
    row = li({"class": 'a&"b'}, "replaced")
    nested: list[Child] = ["雪 & ", p("<inside>")]
    items: list[Child] = ["<one> \"' &", 0, None, nested]
    fragment = row.repeat(item for item in items)
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
    with pytest.raises(TypeError):
        li.repeat(items)


def test_repeat_rejects_void_elements():
    for element in (meta, link):
        for items in ([], [None], ["text"]):
            with pytest.raises(ValueError, match="cannot have children"):
                element.repeat(items)
