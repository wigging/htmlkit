"""Check element construction, attributes, void rules, reuse, and object semantics."""

from copy import copy, deepcopy
from types import MappingProxyType

import pytest

from htmpy import Child, Element, Fragment, Raw, body, link, meta, p


def test_public_construction() -> None:
    """Build elements directly with children and attributes."""
    element = Element("section", "<unsafe>&", p("<nested>"), title='"<&')
    expected = '<section title="&#34;&lt;&amp;">&lt;unsafe&gt;&amp;<p>&lt;nested&gt;</p></section>'
    assert str(element) == expected
    assert str(Element("p", "<unsafe>&")) == "<p>&lt;unsafe&gt;&amp;</p>"
    assert str(Element("p", (), "<unsafe>&")) == "<p>&lt;unsafe&gt;&amp;</p>"
    assert str(element("<next>", title=None)) == "<section>&lt;next&gt;</section>"
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
        Element("p", "text", **attributes)


@pytest.mark.parametrize("tag", ["meta", "link", "img", "br"])
def test_constructor_void(tag: str) -> None:
    """Verify directly constructed void elements render and reject children."""
    element = Element(tag, id="example")
    assert str(element) == f'<{tag} id="example">'
    for child in ("text", "", None, []):
        with pytest.raises(ValueError, match="cannot have children"):
            Element(tag, child)


@pytest.mark.parametrize("element, tag", [(meta, "meta"), (link, "link")])
def test_void_elements(element, tag):
    """Verify void shortcuts support attribute updates but reject all children."""
    assert str(element) == f"<{tag}>"
    assert str(element()) == f"<{tag}>"
    base = element(id="original")
    assert str(base(id="updated", hidden=True, title=None)) == (f'<{tag} id="updated" hidden>')
    assert str(base) == f'<{tag} id="original">'
    assert str(base(id=None)) == f"<{tag}>"
    for child in ("text", "", None, [], (), 0):
        with pytest.raises(ValueError, match=f"The {tag} element cannot have children"):
            element(child)
    with pytest.raises(ValueError, match=f"The {tag} element cannot have children"):
        element(p("child"), id="example")


@pytest.mark.parametrize(
    "element, attrs, expected",
    [
        (p, {"cls": "intro"}, '<p cls="intro"></p>'),
        (p, {"content": "Hello"}, '<p content="Hello"></p>'),
        (meta, {"charset": "utf-8"}, '<meta charset="utf-8">'),
    ],
)
def test_keyword_attributes(element, attrs, expected):
    """Accept keyword attributes without reserving content-related names."""
    assert str(element(**attrs)) == expected


def test_attributes():
    """Verify normalized names and string, numeric, boolean, and null values."""
    assert (
        str(p(class_="intro", data_id=7, hidden=True, title=None, inert=False))
        == '<p class="intro" data-id="7" hidden></p>'
    )
    assert str(p(tabindex=0)) == '<p tabindex="0"></p>'
    assert str(Element("input", type_="number", min=-2.5, max=0.0, step=0.01)) == (
        '<input type="number" min="-2.5" max="0.0" step="0.01">'
    )
    assert str(p(for_="field", aria_label="Name")) == '<p for="field" aria-label="Name"></p>'
    assert str(p("Hello")) == "<p>Hello</p>"
    assert str(Element("p", "Hi", tag="custom", first="one", children="two")) == (
        '<p tag="custom" first="one" children="two">Hi</p>'
    )
    with pytest.raises(TypeError, match="Duplicate HTML attribute"):
        p(class_="one", **{"class": "two"})


@pytest.mark.parametrize(
    "name, normalized", [("ID", "id"), ("Class_", "class"), ("DATA_Key", "data-key")]
)
def test_attribute_case(name: str, normalized: str) -> None:
    """Normalize ASCII case for rendering, collisions, and inherited updates."""
    base = p("Original", **{name: "old", "title": "kept"})
    expected = f'<p {normalized}="old" title="kept">Original</p>'
    assert str(base) == expected
    with pytest.raises(TypeError, match="Duplicate HTML attribute"):
        p(**{name: "old", normalized: "new"})
    assert str(base("Changed", **{normalized: "new"})) == (
        f'<p {normalized}="new" title="kept">Changed</p>'
    )
    for omitted in (None, False):
        assert str(base(**{normalized: omitted})) == '<p title="kept"></p>'
    assert str(base) == expected


def test_generated_attribute_names():
    """Render many distinct runtime attribute names, beyond any internal name cache."""
    names = {f"data_key_{index}": index for index in range(1500)}
    rendered = str(p(**names))
    assert rendered.startswith('<p data-key-0="0" data-key-1="1"')
    assert rendered.count("=") == 1500 and rendered.endswith('data-key-1499="1499"></p>')
    assert str(p(data_key_1499="again")) == '<p data-key-1499="again"></p>'
    with pytest.raises(ValueError, match="Invalid HTML attribute name"):
        p(**{"data_key_1500 onclick": "x"})


def test_positional_attributes() -> None:
    """Reject positional attribute mappings in every position."""
    with pytest.raises(TypeError):
        p("Hello", {"class": "intro"})  # ty: ignore[invalid-argument-type]
    with pytest.raises(TypeError):
        p({"id": "first"})  # ty: ignore[invalid-argument-type]
    with pytest.raises(TypeError):
        Element("p", MappingProxyType({"id": "first"}))  # ty: ignore[invalid-argument-type]


def test_reuse():
    """Verify element calls replace children and merge attributes without mutation."""
    base = p("Original", class_="note")
    changed = base("Changed", class_="new", id="message")
    assert str(base) == '<p class="note">Original</p>'
    assert str(changed) == '<p class="new" id="message">Changed</p>'
    assert str(changed("Kept", class_=None)) == '<p id="message">Kept</p>'
    assert str(changed) == '<p class="new" id="message">Changed</p>'
    assert str(base("Original", class_=None)) == "<p>Original</p>"
    assert str(base("Next & <last>")) == '<p class="note">Next &amp; &lt;last&gt;</p>'
    assert str(base()) == '<p class="note"></p>'
    assert str(p) == "<p></p>"


@pytest.mark.parametrize(
    "element, expected, updated",
    [
        (
            p("A & <B>", class_="note"),
            '<p class="note">A &amp; &lt;B&gt;</p>',
            '<p class="note" id="updated"></p>',
        ),
        (
            meta(charset="utf-8"),
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
        assert str(cloned(id="updated")) == updated
        assert str(cloned) == str(element) == expected


def test_child_snapshot():
    """Verify later changes to child lists do not alter rendered elements."""
    children: list[Child] = [p("First"), (None, " & ", 0)]
    element = body(children)
    children.clear()
    assert str(element) == "<body><p>First</p> &amp; 0</body>"


def test_equality():
    """Verify equality and hashing distinguish markup types and rendered content."""
    assert p("A", id="x") == p("A", id="x") == Element("p", "A", id="x")
    assert p("A") != p("B") and p("A") != Element("div", "A")
    assert Fragment(p("A")) == Fragment(p("A")) != p("A")
    assert Raw("<p>A</p>") != p("A")
    assert p("A") != "<p>A</p>"
    assert len({p("A"), p("A"), Fragment(p("A")), Raw("<p>A</p>")}) == 3
    assert repr(p("A & B")) == "Element('<p>A &amp; B</p>')"
