import unittest

from htmpy import Child, body, h1, head, html, p


class ElementTests(unittest.TestCase):
    def test_document(self):
        page = html({"lang": "en"}, head(), body(h1("Hello"), p("First"), p("Second")))
        self.assertEqual(
            str(page),
            '<!doctype html><html lang="en"><head></head><body>'
            "<h1>Hello</h1><p>First</p><p>Second</p></body></html>",
        )
        for element, tag in ((head, "head"), (body, "body"), (h1, "h1"), (p, "p")):
            with self.subTest(tag=tag):
                self.assertEqual(str(element()), f"<{tag}></{tag}>")
        self.assertEqual(str(html()), "<!doctype html><html></html>")

    def test_escaping(self):
        self.assertEqual(
            str(p({"title": "\"<&'"}, "<script>alert('x')</script> &")),
            "<p title=\"&quot;&lt;&amp;&#x27;\">&lt;script&gt;alert('x')&lt;/script&gt; &amp;</p>",
        )
        with self.assertRaises(ValueError):
            p({'x="injected"': "value"})

    def test_attributes(self):
        self.assertEqual(
            str(p({"class": "intro", "data-id": 7, "hidden": True, "title": None, "inert": False})),
            '<p class="intro" data-id="7" hidden></p>',
        )
        self.assertEqual(str(p({"tabindex": 0})), '<p tabindex="0"></p>')
        self.assertEqual(str(p({"data_id": "literal"})), '<p data_id="literal"></p>')
        self.assertEqual(str(p({}, "Hello")), "<p>Hello</p>")

    def test_attributes_must_come_first(self):
        with self.assertRaises(TypeError):
            p("Hello", {"class": "intro"})
        with self.assertRaises(TypeError):
            p({"id": "first"}, {"class": "intro"})

    def test_reuse_and_replacement(self):
        base = p({"class": "note"}, "Original")
        changed = base({"class": "new", "id": "message"}, "Changed")
        self.assertEqual(str(base), '<p class="note">Original</p>')
        self.assertEqual(str(changed), '<p class="new" id="message">Changed</p>')
        self.assertEqual(str(base({"class": None}, "Original")), "<p>Original</p>")
        self.assertEqual(str(p), "<p></p>")

    def test_nested_children_are_snapshotted(self):
        children: list[Child] = [p("First"), (None, " & ", 0)]
        element = body(children)
        children.clear()
        self.assertEqual(str(element), "<body><p>First</p> &amp; 0</body>")
        self.assertEqual(str(element), "<body><p>First</p> &amp; 0</body>")

    def test_mixed_content_and_attribute_snapshot(self):
        attributes = {"class": "intro"}
        element = body(attributes, "Before ", p("inside"), " after.")
        attributes["class"] = "changed"
        self.assertEqual(str(element), '<body class="intro">Before <p>inside</p> after.</body>')


if __name__ == "__main__":
    unittest.main()
