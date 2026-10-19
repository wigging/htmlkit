"""Check fragment construction, nesting, snapshots, and repeated elements."""

from copy import copy, deepcopy

import pytest

from htmpy import Child, Fragment, body, li, link, meta, p, ul


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
