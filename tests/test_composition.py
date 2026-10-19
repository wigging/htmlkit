"""Check fragment construction, nesting, snapshots, and repeated elements."""

from copy import copy, deepcopy

import pytest

from htmpy import Child, Fragment, article, body, br, div, li, link, meta, p, section, span, ul


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
    for cloned in (copy(fragment), deepcopy(fragment)):
        assert isinstance(cloned, Fragment)
        assert str(body(cloned)) == f"<body>{expected}</body>"


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
    for cloned in (copy(fragment), deepcopy(fragment)):
        assert str(ul(cloned)) == f"<ul>{expected}</ul>"


def test_nested_wrappers():
    """Verify single-element wrapping renders mixed tags, runs, branches, and copies."""
    inner = div(div(p("a & <b>")))
    expected = "<div><div><p>a &amp; &lt;b&gt;</p></div></div>"
    boxed = div({"class": "box"})
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
    assert str(div({"id": "x"}, inner)) == f'<div id="x">{expected}</div>'
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


def test_repeat_rejects_void_elements():
    """Reject repeating void elements even with an empty iterable."""
    for element in (meta, link):
        for items in ([], [None], ["text"]):
            with pytest.raises(ValueError, match="cannot have children"):
                element.repeat(items)
