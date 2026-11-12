"""Check HTML tag exports, names, and rendering behavior."""

import builtins
import keyword

import pytest

import htmlkit
from htmlkit import Element, div, html, input_, map_, object_, p, tags

VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "track",
    "wbr",
}


@pytest.mark.parametrize("name", tags.__all__)
def test_tag_renders_its_html_name(name):
    """Verify each exported tag renders its HTML name and accepts attributes."""
    element = getattr(tags, name)
    tag = name.rstrip("_")
    assert isinstance(element, Element)
    assert getattr(htmlkit, name) is element
    if tag in VOID:
        assert str(element) == f"<{tag}>"
        with pytest.raises(ValueError, match="cannot have children"):
            element("text")
    elif tag == "html":
        assert str(element) == "<!doctype html><html></html>"
    else:
        assert str(element("<")) == f"<{tag}>&lt;</{tag}>"
    prefix = "<!doctype html>" if tag == "html" else ""
    closing = "" if tag in VOID else f"</{tag}>"
    assert str(element(id="x")) == f'{prefix}<{tag} id="x">{closing}'


def test_tag_module_covers_the_living_standard():
    """Verify tag coverage, unique exports, and Python-safe names."""
    assert len(tags.__all__) == 113
    assert len(set(tags.__all__)) == len(tags.__all__)
    assert tags.del_ is not None and "del" not in tags.__all__
    assert not any(keyword.iskeyword(name) for name in tags.__all__)
    assert not set(tags.__all__) & set(dir(builtins))
    for name in ("title", "script", "style", "form", "input_", "table", "nav", "span", "img"):
        assert name in tags.__all__
    assert all(name in htmlkit.__all__ for name in tags.__all__)
    assert "svg" not in tags.__all__ and "math" not in tags.__all__


def test_import_styles():
    """Expose the same Python-safe elements through named and package imports."""
    assert html(div(p("Hi", class_="intro")), lang="en") == htmlkit.html(
        htmlkit.div(htmlkit.p("Hi", class_="intro")), lang="en"
    )
    assert str(map_(object_(input_(type_="text")), name="locations")) == (
        '<map name="locations"><object><input type="text"></object></map>'
    )
    for name in ("input", "map", "object", "del"):
        assert not hasattr(htmlkit, name)
        assert not hasattr(tags, name)


def test_html_shortcut_for_custom_tags_is_consistent():
    """Verify direct construction matches shortcuts and validates custom tags."""
    assert str(Element("section", "x")) == str(tags.section("x")) == "<section>x</section>"
    assert str(Element("my-widget", "x")) == "<my-widget>x</my-widget>"
    with pytest.raises(ValueError, match="Invalid HTML tag name"):
        Element("My-Widget")
