import pytest

from htmpy import Child, body, h1, head, html, p


def test_document():
    page = html({"lang": "en"}, head(), body(h1("Hello"), p("First"), p("Second")))
    assert str(page) == (
        '<!doctype html><html lang="en"><head></head><body>'
        "<h1>Hello</h1><p>First</p><p>Second</p></body></html>"
    )
    assert str(html()) == "<!doctype html><html></html>"


@pytest.mark.parametrize("element, tag", [(head, "head"), (body, "body"), (h1, "h1"), (p, "p")])
def test_empty(element, tag):
    assert str(element()) == f"<{tag}></{tag}>"


def test_escaping():
    assert str(p({"title": "\"<&'"}, "<script>alert('x')</script> &")) == (
        "<p title=\"&quot;&lt;&amp;&#x27;\">&lt;script&gt;alert('x')&lt;/script&gt; &amp;</p>"
    )
    with pytest.raises(ValueError):
        p({'x="injected"': "value"})


def test_attributes():
    assert str(
        p({"class": "intro", "data-id": 7, "hidden": True, "title": None, "inert": False})
    ) == '<p class="intro" data-id="7" hidden></p>'
    assert str(p({"tabindex": 0})) == '<p tabindex="0"></p>'
    assert str(p({"data_id": "literal"})) == '<p data_id="literal"></p>'
    assert str(p({}, "Hello")) == "<p>Hello</p>"


def test_attribute_order():
    with pytest.raises(TypeError):
        p("Hello", {"class": "intro"})
    with pytest.raises(TypeError):
        p({"id": "first"}, {"class": "intro"})


def test_reuse():
    base = p({"class": "note"}, "Original")
    changed = base({"class": "new", "id": "message"}, "Changed")
    assert str(base) == '<p class="note">Original</p>'
    assert str(changed) == '<p class="new" id="message">Changed</p>'
    assert str(base({"class": None}, "Original")) == "<p>Original</p>"
    assert str(p) == "<p></p>"


def test_child_snapshot():
    children: list[Child] = [p("First"), (None, " & ", 0)]
    element = body(children)
    children.clear()
    assert str(element) == "<body><p>First</p> &amp; 0</body>"
    assert str(element) == "<body><p>First</p> &amp; 0</body>"


def test_attribute_snapshot():
    attributes = {"class": "intro"}
    element = body(attributes, "Before ", p("inside"), " after.")
    attributes["class"] = "changed"
    assert str(element) == '<body class="intro">Before <p>inside</p> after.</body>'
