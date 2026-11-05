"""Check text and attribute escaping and trusted raw HTML insertion."""

from copy import copy, deepcopy

import pytest
from markupsafe import Markup

from htmpy import Fragment, Raw, each, li, p, script, ul


def test_escaping():
    """Verify text and attribute escaping without double-escaping nested elements."""
    assert str(p("雪 & <tag> \"'")) == "<p>雪 &amp; &lt;tag&gt; &#34;&#39;</p>"
    # Long text takes a different escaping path and must produce the same entities.
    phrase = "She said \"A & B\" <twice> and 'left'. "
    escaped = "She said &#34;A &amp; B&#34; &lt;twice&gt; and &#39;left&#39;. "
    assert str(p(phrase * 4, title=phrase * 4)) == f'<p title="{escaped * 4}">{escaped * 4}</p>'
    child = li("<one> & two")
    assert str(ul([child, str(child)])) == (
        "<ul><li>&lt;one&gt; &amp; two</li>"
        "&lt;li&gt;&amp;lt;one&amp;gt; &amp;amp; two&lt;/li&gt;</ul>"
    )
    assert str(p("<script>alert('x')</script> &", title="\"<&'")) == (
        '<p title="&#34;&lt;&amp;&#39;">&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt; &amp;</p>'
    )
    with pytest.raises(ValueError):
        p(**{'x="injected"': "value"})


def test_bound_attribute_escaping() -> None:
    """Escape interpolated attributes without changing trusted child rendering."""
    value = Markup('<b>" onmouseover="alert(1) &</b>')
    row = p(
        each[0],
        title="prefix & " + each[0] + " / " + each[1] + " suffix",
        data_value=each[0],
    )
    escaped = "&lt;b&gt;&#34; onmouseover=&#34;alert(1) &amp;&lt;/b&gt;"
    assert str(row.repeat([(value, "<second>"), (str(value), "last &")])) == (
        f'<p title="prefix &amp; {escaped} / &lt;second&gt; suffix" data-value="{escaped}">'
        '<b>" onmouseover="alert(1) &</b></p>'
        f'<p title="prefix &amp; {escaped} / last &amp; suffix" data-value="{escaped}">'
        f"{escaped}</p>"
    )
    for child in (Raw('" onclick="alert(1)'), p("nested"), Fragment("text")):
        with pytest.raises(TypeError, match="Unsupported HTML attribute value"):
            p(title="prefix " + each[0]).repeat([(child,)])


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
    for cloned in (copy(Raw("<br>")), deepcopy(Raw("<br>"))):
        assert isinstance(cloned, Raw)
        assert str(cloned) == "<br>"
    with pytest.raises(TypeError):
        Raw(p("not a string"))  # ty: ignore[invalid-argument-type]
