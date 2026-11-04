"""Check fragment construction, nesting, snapshots, and repeated elements."""

from copy import copy, deepcopy
from operator import itemgetter
from types import SimpleNamespace
from typing import NamedTuple

import pytest

from htmpy import (
    Child,
    Element,
    Fragment,
    Raw,
    a,
    article,
    bind,
    body,
    br,
    div,
    each,
    input_,
    li,
    link,
    meta,
    p,
    section,
    span,
    td,
    tr,
    ul,
)


def test_fragment() -> None:
    """Escape and nest children without a wrapping tag."""
    fragment = Fragment("<unsafe> & ", p("雪"), (None, 0, ["café"]))
    expected = "&lt;unsafe&gt; &amp; <p>雪</p>0café"
    assert str(fragment) == expected
    assert str(Fragment()) == str(Fragment.from_iterable([])) == ""
    assert str(body(Fragment(fragment, "!"))) == f"<body>{expected}!</body>"
    assert str(Fragment(str(p("<&")))) == "&lt;p&gt;&amp;lt;&amp;amp;&lt;/p&gt;"


def test_fragment_snapshot() -> None:
    """Consume iterable children immediately and retain their rendered content."""
    children: list[Child] = ["<unsafe> & ", p("雪"), (None, 0, ["café"])]
    generated = (child for child in children)
    fragment = Fragment.from_iterable(generated)
    assert list(generated) == []
    children.clear()
    assert str(fragment) == "&lt;unsafe&gt; &amp; <p>雪</p>0café"


def test_fragment_copy() -> None:
    """Copy fragments without escaping their content again."""
    fragment = Fragment("<&", p("nested"))
    for cloned in (copy(fragment), deepcopy(fragment)):
        assert isinstance(cloned, Fragment)
        assert str(body(cloned)) == "<body>&lt;&amp;<p>nested</p></body>"


@pytest.mark.parametrize("child", [{"id": "not-attributes"}, object()])
def test_fragment_rejects_invalid_children(child):
    """Reject mappings and unsupported objects as fragment children."""
    with pytest.raises(TypeError):
        Fragment(child)
    with pytest.raises(TypeError):
        Fragment.from_iterable([child])


@pytest.mark.parametrize("container", [p, Fragment])
def test_generator_children_rejected(container):
    """Require explicit iterable APIs rather than accepting generators as children."""
    children = (text for text in ["<one>", " & two"])
    with pytest.raises(TypeError, match="Unsupported HTML child"):
        container(children)
    assert str(Fragment.from_iterable(children)) == "&lt;one&gt; &amp; two"


def test_repeat():
    """Verify repeated elements snapshot content and retain the base attributes."""
    row = li("replaced", class_='a&"b')
    nested: list[Child] = ["雪 & ", p("<inside>")]
    items: list[Child] = ["<one> \"' &", 0, None, nested]
    fragment = row.repeat(item for item in items)
    assert isinstance(fragment, Fragment)
    items.clear()
    nested.clear()
    expected = (
        '<li class="a&amp;&#34;b">&lt;one&gt; &#34;&#39; &amp;</li>'
        '<li class="a&amp;&#34;b">0</li>'
        '<li class="a&amp;&#34;b"></li>'
        '<li class="a&amp;&#34;b">雪 &amp; <p>&lt;inside&gt;</p></li>'
    )
    assert str(fragment) == expected
    assert str(ul(fragment)) == f"<ul>{expected}</ul>"
    assert str(body("Before ", [fragment, (fragment,)], " after")) == (
        f"<body>Before {expected}{expected} after</body>"
    )
    assert str(p.repeat([fragment])) == f"<p>{expected}</p>"
    assert str(row) == '<li class="a&amp;&#34;b">replaced</li>'
    assert str(ul(li.repeat([]))) == "<ul></ul>"
    assert str(ul(str(li.repeat(["<unsafe>"])))) == (
        "<ul>&lt;li&gt;&amp;lt;unsafe&amp;gt;&lt;/li&gt;</ul>"
    )


def test_nested_wrappers():
    """Verify single-element wrapping renders mixed tags, runs, branches, and copies."""
    inner = div(div(p("a & <b>")))
    expected = "<div><div><p>a &amp; &lt;b&gt;</p></div></div>"
    boxed = div(class_="box")
    chain = article(section(boxed(boxed(inner))))
    assert str(chain) == (
        f'<article><section><div class="box"><div class="box">{expected}</div></div>'
        "</section></article>"
    )
    assert str(inner) == expected
    # Wrapping the same child twice must not alter the child or the sibling branch.
    first, second = div(inner), span(inner)
    assert str(first) == f"<div>{expected}</div>"
    assert str(second) == f"<span>{expected}</span>"
    assert str(inner) == expected
    assert str(body(chain, " & ", second)) == f"<body>{chain} &amp; {second}</body>"
    assert str(div(inner, id="x")) == f'<div id="x">{expected}</div>'
    assert str(div(br)) == "<div><br></div>"
    assert str(inner("replaced")) == "<div>replaced</div>"
    flat = div(div(p("a & <b>")), None)
    assert inner == flat and hash(inner) == hash(flat)
    assert repr(inner) == f"Element({expected!r})"
    for cloned in (copy(chain), deepcopy(chain)):
        assert str(cloned) == str(chain)
    with pytest.raises(AttributeError, match="no attribute 'missing'"):
        inner.missing  # noqa: B018


@pytest.mark.parametrize("items", [[{"id": "not-an-attribute-update"}], [object()]])
def test_repeat_rejects_invalid_content(items):
    """Reject mappings and unsupported objects as repeated content."""
    with pytest.raises(TypeError):
        li.repeat(items)


@pytest.mark.parametrize("element", [meta, link])
@pytest.mark.parametrize("items", [[], [None], ["text"]])
def test_repeat_rejects_void_elements(element: Element, items: list[Child]) -> None:
    """Reject repeating void elements even with an empty iterable."""
    with pytest.raises(ValueError, match="cannot have children"):
        element.repeat(items)


class Item(NamedTuple):
    """A record for template tests."""

    id: int
    name: str
    href: str
    active: bool
    note: str | None


ITEMS = [
    Item(1, "A & <b>", "/a?x=1&y=2", True, None),
    Item(2, "雪", "/b", False, 'say "hi"'),
]


def test_repeat_template() -> None:
    """Fill bound children and attributes from each item in one call."""
    row = tr(
        td(each.id, class_="row " + each.name),
        td(a(each.name, href=each.href), hidden=each(lambda item: not item.active)),
        td(each(lambda item: item.id * 2), " {literal}", title=each.note),
        id=each(lambda item: f"row-{item.id}"),
    )
    fragment = row.repeat(iter(ITEMS))
    assert isinstance(fragment, Fragment)
    assert str(fragment) == (
        '<tr id="row-1"><td class="row A &amp; &lt;b&gt;">1</td>'
        '<td><a href="/a?x=1&amp;y=2">A &amp; &lt;b&gt;</a></td>'
        "<td>2 {literal}</td></tr>"
        '<tr id="row-2"><td class="row 雪">2</td>'
        '<td hidden><a href="/b">雪</a></td>'
        '<td title="say &#34;hi&#34;">4 {literal}</td></tr>'
    )
    assert str(row.repeat([])) == ""
    # Templates compose: a bound value may itself be a repeated fragment or an element.
    groups = [("Fruit", ["Apple", "Pear & fig"]), ("Empty", [])]
    nested = li(each[0], ul(each(lambda group: li.repeat(group[1]))))
    assert str(ul(nested.repeat(groups))) == (
        "<ul><li>Fruit<ul><li>Apple</li><li>Pear &amp; fig</li></ul></li>"
        "<li>Empty<ul></ul></li></ul>"
    )
    assert str(p(each).repeat(["<x>", 0, None, span("y"), Raw("<i>")])) == (
        "<p>&lt;x&gt;</p><p>0</p><p></p><p><span>y</span></p><p><i></p>"
    )
    assert str(p(bind()).repeat(["<x>"])) == "<p>&lt;x&gt;</p>"


def test_repeat_integers() -> None:
    """Render integers without bypassing escaping or HTML hooks on subclasses."""

    class _TextInt(int):
        def __str__(self) -> str:
            return "<one & two>"

    class _HtmlInt(int):
        def __html__(self) -> str:
            return "<b>three</b>"

    assert str(p(each).repeat([0, -12, 10**30, True, False, _TextInt(1), _HtmlInt(3)])) == (
        "<p>0</p><p>-12</p><p>1000000000000000000000000000000</p>"
        "<p>True</p><p>False</p><p>&lt;one &amp; two&gt;</p><p><b>three</b></p>"
    )


def test_repeat_reentrant() -> None:
    """Keep outer row content intact when a binding fills the same template."""
    row = p(
        each[0],
        title=each(lambda item: str(row.repeat([("inner", False)])) if item[1] else None),
    )
    assert str(row.repeat([("outer &", True), ("last", False)])) == (
        '<p title="&lt;p&gt;inner&lt;/p&gt;">outer &amp;</p><p>last</p>'
    )
    assert str(row.repeat([("again", False)])) == "<p>again</p>"


def test_repeat_template_attributes() -> None:
    """Drop, flag, or quote whole bound attributes, including on void elements."""
    field = input_(name=each.name, disabled=each.active, value=each.id)
    assert str(field.repeat(ITEMS)) == (
        '<input name="A &amp; &lt;b&gt;" disabled value="1"><input name="雪" value="2">'
    )
    assert str(td(each.id, title=each.note).repeat(ITEMS)) == (
        '<td>1</td><td title="say &#34;hi&#34;">2</td>'
    )
    with pytest.raises(TypeError, match="Unsupported HTML attribute value"):
        td(title=each(lambda item: [item])).repeat(ITEMS)


def test_each_and_bind() -> None:
    """Share placeholders per accessor and reject accessors that cannot read an item."""
    assert each.name == bind("name") == each("name") and each.name != each.id
    assert each[0] != each["0"] != each("0")
    assert repr(each) == "each"
    assert str(td(each("owner.name")).repeat([SimpleNamespace(owner=ITEMS[1])])) == "<td>雪</td>"
    assert str(td(each[1], each["count"]).repeat([{1: "a&", "count": 3}])) == "<td>a&amp;3</td>"
    assert str(td(each[0], bind(itemgetter(1))).repeat([("x", "y")])) == "<td>xy</td>"
    with pytest.raises(TypeError, match="Unsupported binding accessor"):
        bind(1.5)  # ty: ignore[invalid-argument-type]
    with pytest.raises(AttributeError):
        td(each.missing).repeat(ITEMS)
    with pytest.raises(AttributeError):
        each.__missing__  # noqa: B018
    # A placeholder is only filled by repeat(); other renders keep it as a marker.
    assert "\x00" in str(td(bind("id")))
