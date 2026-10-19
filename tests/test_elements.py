"""Check element construction, attributes, void rules, reuse, and object semantics."""

from copy import copy, deepcopy
from types import MappingProxyType

import pytest

from htmpy import Child, Element, Fragment, Raw, body, link, meta, p


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
    for cloned in (copy(element), deepcopy(element)):
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
    for cloned in (copy(element), deepcopy(element)):
        assert str(cloned) == str(element)


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
    assert str(changed({"class": None}, "Kept")) == '<p id="message">Kept</p>'
    assert str(changed) == '<p class="new" id="message">Changed</p>'
    assert str(base({"class": None}, "Original")) == "<p>Original</p>"
    assert str(base("Next & <last>")) == '<p class="note">Next &amp; &lt;last&gt;</p>'
    assert str(base()) == '<p class="note"></p>'
    assert str(p) == "<p></p>"


@pytest.mark.parametrize(
    "element, expected, updated",
    [
        (
            p({"class": "note"}, "A & <B>"),
            '<p class="note">A &amp; &lt;B&gt;</p>',
            '<p class="note" id="updated"></p>',
        ),
        (
            meta({"charset": "utf-8"}),
            '<meta charset="utf-8">',
            '<meta charset="utf-8" id="updated">',
        ),
    ],
)
def test_element_copy(element, expected, updated):
    """Verify shallow and deep copying preserve rendering and attribute updates."""
    for cloned in (copy(element), deepcopy(element)):
        assert isinstance(cloned, Element)
        assert str(cloned) == expected
        assert str(cloned({"id": "updated"})) == updated
        assert str(cloned) == str(element) == expected


def test_child_snapshot():
    """Verify later changes to child lists do not alter rendered elements."""
    children: list[Child] = [p("First"), (None, " & ", 0)]
    element = body(children)
    children.clear()
    assert str(element) == "<body><p>First</p> &amp; 0</body>"


def test_attribute_snapshot():
    """Verify later changes to attribute mappings do not alter rendered elements."""
    attributes = {"class": "intro"}
    element = body(attributes, "Before ", p("inside"), " after.")
    attributes["class"] = "changed"
    assert str(element) == '<body class="intro">Before <p>inside</p> after.</body>'


def test_equality():
    """Verify equality and hashing distinguish markup types and rendered content."""
    assert p({"id": "x"}, "A") == p({"id": "x"}, "A") == Element("p", {"id": "x"}, "A")
    assert p("A") != p("B") and p("A") != Element("div", "A")
    assert Fragment(p("A")) == Fragment(p("A")) != p("A")
    assert Raw("<p>A</p>") != p("A")
    assert p("A") != "<p>A</p>"
    assert len({p("A"), p("A"), Fragment(p("A")), Raw("<p>A</p>")}) == 3
    assert repr(p("A & B")) == "Element('<p>A &amp; B</p>')"
