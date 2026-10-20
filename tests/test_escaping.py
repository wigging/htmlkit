"""Check text and attribute escaping and trusted raw HTML insertion."""

from copy import copy, deepcopy

import pytest

from htmpy import Fragment, Raw, li, p, script, ul


def test_escaping():
    """Verify text and attribute escaping without double-escaping nested elements."""
    assert str(p("雪 & <tag> \"'")) == "<p>雪 &amp; &lt;tag&gt; \"'</p>"
    child = li("<one> & two")
    assert str(ul([child, str(child)])) == (
        "<ul><li>&lt;one&gt; &amp; two</li>"
        "&lt;li&gt;&amp;lt;one&amp;gt; &amp;amp; two&lt;/li&gt;</ul>"
    )
    assert str(p("<script>alert('x')</script> &", title="\"<&'")) == (
        "<p title=\"&quot;&lt;&amp;&#x27;\">&lt;script&gt;alert('x')&lt;/script&gt; &amp;</p>"
    )
    with pytest.raises(ValueError):
        p(**{'x="injected"': "value"})


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
