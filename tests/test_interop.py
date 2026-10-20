"""Check HTML encoding, FastAPI responses, and HTML protocol interoperability."""

import pytest
from fastapi.responses import HTMLResponse
from jinja2 import Environment
from markupsafe import Markup

from htmpy import Fragment, Raw, body, html, p


@pytest.mark.parametrize("kind", ["element", "fragment", "raw"])
def test_html_response(kind):
    """Verify all markup types work directly as UTF-8 FastAPI response content."""
    page = html(body(p("雪 & <hello>", title='"café"')))
    if kind == "fragment":
        page = Fragment(page)
    elif kind == "raw":
        page = Raw(
            '<!doctype html><html><body><p title="&#34;café&#34;">'
            "雪 &amp; &lt;hello&gt;</p></body></html>"
        )
    response = HTMLResponse(page, status_code=201)
    expected = (
        '<!doctype html><html><body><p title="&#34;café&#34;">'
        "雪 &amp; &lt;hello&gt;</p></body></html>"
    ).encode()
    assert response.body == expected
    assert response.status_code == 201
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["content-length"] == str(len(expected))


@pytest.mark.parametrize("element", [p("café"), Fragment(p("café")), Raw("<p>café</p>")])
def test_encode(element):
    """Verify encoding choices and error handling for rendered HTML."""
    assert element.encode() == b"<p>caf\xc3\xa9</p>"
    assert element.encode("latin-1") == b"<p>caf\xe9</p>"
    assert element.encode("ascii", errors="xmlcharrefreplace") == b"<p>caf&#233;</p>"
    with pytest.raises(UnicodeEncodeError):
        element.encode("ascii")


def test_html_protocol():
    """Verify HTML protocol interoperability with custom objects, Markup, and Jinja."""

    class Widget:
        def __html__(self) -> str:
            return "<widget>&</widget>"

    assert str(p(Widget())) == "<p><widget>&</widget></p>"
    assert str(p(Markup("<b>safe</b>"), "<unsafe>")) == "<p><b>safe</b>&lt;unsafe&gt;</p>"
    assert str(Fragment.from_iterable([Widget(), Markup("&amp;")])) == "<widget>&</widget>&amp;"
    assert p("A & B").__html__() == "<p>A &amp; B</p>"
    assert Fragment("<").__html__() == "&lt;"
    template = Environment(autoescape=True).from_string("<div>{{ content }}</div>")
    for content in (p("A & B"), Fragment(p("A & B")), Raw("<p>A &amp; B</p>")):
        assert template.render(content=content) == "<div><p>A &amp; B</p></div>"
    assert template.render(content=str(p("A & B"))) == "<div>&lt;p&gt;A &amp;amp; B&lt;/p&gt;</div>"
