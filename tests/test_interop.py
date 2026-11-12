"""Check encoding and the HTML protocol through htmlkit's public API."""

import pytest
from markupsafe import Markup

from htmlkit import Element, Fragment, Raw, p


@pytest.mark.parametrize("element", [p("café"), Fragment(p("café")), Raw("<p>café</p>")])
def test_encode(element: Element | Fragment | Raw) -> None:
    """Verify encoding choices and error handling for rendered HTML."""
    assert element.encode() == b"<p>caf\xc3\xa9</p>"
    assert element.encode("latin-1") == b"<p>caf\xe9</p>"
    assert element.encode("ascii", errors="xmlcharrefreplace") == b"<p>caf&#233;</p>"
    with pytest.raises(UnicodeEncodeError):
        element.encode("ascii")


def test_html_children() -> None:
    """Insert HTML protocol objects without escaping their trusted markup."""

    class _Widget:
        def __html__(self) -> str:
            return "<widget>&</widget>"

    assert str(p(_Widget())) == "<p><widget>&</widget></p>"
    assert str(p(Markup("<b>safe</b>"), "<unsafe>")) == "<p><b>safe</b>&lt;unsafe&gt;</p>"
    assert str(Fragment.from_iterable([_Widget(), Markup("&amp;")])) == "<widget>&</widget>&amp;"


@pytest.mark.parametrize("content", [p("A & B"), Fragment(p("A & B")), Raw("<p>A &amp; B</p>")])
def test_html_protocol(content: Element | Fragment | Raw) -> None:
    """Expose rendered markup as trusted HTML for template consumers."""
    assert content.__html__() == "<p>A &amp; B</p>"
