import keyword

import pytest

import htmpy
from htmpy import Element, tags

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
    element = getattr(tags, name)
    tag = name.rstrip("_")
    assert isinstance(element, Element)
    assert getattr(htmpy, name) is element
    if tag in VOID:
        assert str(element) == f"<{tag}>"
        with pytest.raises(ValueError, match="cannot have children"):
            element("text")
    elif tag == "html":
        assert str(element) == "<!doctype html><html></html>"
    else:
        assert str(element("<")) == f"<{tag}>&lt;</{tag}>"
    assert f'<{tag} id="x">' in str(element({"id": "x"}))


def test_tag_module_covers_the_living_standard():
    assert len(tags.__all__) == 113
    assert len(set(tags.__all__)) == len(tags.__all__)
    assert tags.del_ is not None and "del" not in tags.__all__
    assert not any(keyword.iskeyword(name) for name in tags.__all__)
    for name in ("title", "script", "style", "form", "input", "table", "nav", "span", "img"):
        assert name in tags.__all__
    assert all(name in htmpy.__all__ for name in tags.__all__)
    assert "svg" not in tags.__all__ and "math" not in tags.__all__


def test_html_shortcut_for_custom_tags_is_consistent():
    assert str(Element("section", "x")) == str(tags.section("x")) == "<section>x</section>"
    assert str(Element("my-widget", "x")) == "<my-widget>x</my-widget>"
    with pytest.raises(ValueError, match="Invalid HTML tag name"):
        Element("My-Widget")
