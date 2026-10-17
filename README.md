# htmpy

Write HTML in Python. Requires Python 3.14 or newer, with no runtime dependencies.
Pass an optional attribute dictionary first, followed by child elements or text.

```python
from htmpy import html, head, body, h1, p

page = html(
    {"lang": "en"},
    head(),
    body(
        h1("Hello from Python"),
        p({"class": "intro"}, "Write HTML with htmpy."),
    ),
)

print(page)
```

Output (rendered without extra whitespace):

```html
<!doctype html><html lang="en"><head></head><body><h1>Hello from Python</h1><p class="intro">Write HTML with htmpy.</p></body></html>
```

## Elements and content

Every conforming element in the HTML Living Standard is available by its tag name,
from `html`, `head`, `title`, and `body` through `form`, `input`, `table`, `script`,
and `dialog`. The `del` element is named `del_` because `del` is a Python keyword;
the foreign `svg` and `math` elements are omitted. Call an element with an optional
leading attribute dictionary and any number of children.
Omit the dictionary when no attributes are needed. Convert an element to HTML with
`str(element)` or `print(element)`. The `html` element includes the HTML5 doctype.

For custom elements, use `Element("my-widget", {"class": "note"}, "Text", p("Child"))`.
Import `Element` from `htmpy`. Its positional arguments after the tag follow the
same rules as tag calls: an optional leading mapping, then escaped children.
Tag names must match `[a-z][a-z0-9-]*`; standard HTML void tags reject children.
Tag and attribute names must still be trusted: escaping is not an HTML or
JavaScript sanitizer.

Use `ul` for unordered lists, `ol` for ordered lists, and `li` for their items.
Lists can be nested inside list items:

```python
from htmpy import ul, ol, li

items = ul(
    li("Apples"),
    li("Steps", ol({"start": 2}, li("Prepare"), li("Serve"))),
)
```

For repeated elements, use `repeat()` to avoid constructing an element object
for every item:

```python
items = ul(li.repeat(["Apples", "Pears & peaches"]))

row = li({"class": "result"})
items = ul(row.repeat(name for name in ["Alice", "Bob"]))
```

`repeat()` immediately consumes an iterable and returns an immutable `Fragment`
that can be passed as a child or rendered with `str()`. Each item becomes
one element, reusing the receiver's attributes and replacing its original children.
Items may be text, integers, elements, fragments, `None`, or nested lists and
tuples of children. `None` creates an empty element; an empty iterable creates an
empty fragment. Text is escaped normally, and later input mutations do not affect
the fragment. Dictionaries are not supported as items; configure shared attributes
on the receiver instead. Void elements (`meta` and `link`) reject `repeat()`, even
for an empty iterable. Pass fragments directly as children: converting one to
`str` first makes it ordinary text, which will be escaped again.

Use `Fragment` to group children without adding a wrapping tag:

```python
from htmpy import Fragment, h1, p

content = Fragment(h1("Welcome"), p("A & B"))
paragraphs = Fragment.from_iterable(p(name) for name in ["Alice", "Bob"])
```

`Fragment(*children)` accepts the same children as elements, but no attribute
mapping. Strings are escaped, not treated as raw HTML. `from_iterable()` consumes
its input immediately; later input mutations do not change the fragment.
Generators are accepted through `from_iterable()`, not as ordinary children.
Both forms support empty input. Fragments support `str()` and `encode()` just
like elements, and can be nested inside elements or other fragments.

Use `meta` and `link` inside `head` for metadata and linked resources:

```python
from htmpy import head, meta, link

metadata = head(
    meta({"charset": "utf-8"}),
    meta({"name": "viewport", "content": "width=device-width, initial-scale=1"}),
    link({"rel": "stylesheet", "href": "/styles.css"}),
)
```

These are void elements: they render without closing tags and reject child
arguments with `ValueError` (including `None` or empty lists).

Children can be text, integers, other elements, or nested lists and tuples of
children. `None` produces no content. Text and attribute values are escaped
automatically; strings are never treated as raw HTML.

```python
str(p("A < B & C"))
# '<p>A &lt; B &amp; C</p>'

str(p({"class": "note", "data-id": 7}, "Note"))
# '<p class="note" data-id="7">Note</p>'
```

Attribute names are literal HTML names, such as `"class"` and `"data-id"`; no
underscore conversion is performed. The attribute dictionary must come first.
Keyword attributes and square-bracket children are not supported.
Values can be strings, integers, booleans, or `None`: `True` emits a bare
attribute, while `False` and `None` omit it. Attribute escaping does not make
untrusted JavaScript or other executable attribute values safe.

Elements are reusable: each call creates a new element. Calling an existing
element merges attributes and replaces its children. Text and elements may be
mixed as consecutive children; spaces must be included in the text explicitly.
Children are rendered when attached and attributes are copied, so later changes
to an input list or dictionary do not change an existing element. Elements,
fragments, and raw markup compare equal when they render the same HTML.
This foundation does not validate HTML nesting or provide a command-line interface.

## Trusted HTML

Use `Raw` for markup that must not be escaped, such as inline scripts and styles.
Escaping would otherwise turn `<` and `&` in JavaScript into entities, which
browsers do not decode inside `<script>`:

```python
from htmpy import Raw, head, script, style

head(
    style(Raw("body > main { margin: 0 auto }")),
    script(Raw("if (a < b && c) { go(); }")),
)
```

`Raw` is never validated or sanitized; pass only markup the application controls.
Converting a `Raw`, `Fragment`, or element to `str` first makes it ordinary text
that will be escaped again.

Elements, fragments, and `Raw` implement the `__html__()` protocol shared by
MarkupSafe, Jinja, and Django, and any child object with an `__html__()` method
is inserted without escaping. An htmpy element can therefore be passed to an
autoescaping Jinja template, and a `markupsafe.Markup` value can be used as a
child, which allows migrating a template-based application page by page.

## FastAPI

Pass an element, fragment, or `Raw` directly to FastAPI's `HTMLResponse`. All provide an
`encode()` method that renders escaped HTML and encodes it as UTF-8 by default.
FastAPI is not a runtime dependency of htmpy; install it separately in your app.

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from htmpy import html, body, h1, p

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index():
    page = html(body(h1("Hello"), p("Built with htmpy.")))
    return HTMLResponse(page)
```

Return the `HTMLResponse` itself, rather than a bare element, to bypass FastAPI's
JSON serialization. Alternatively, return `str(page)` from a route declared with
`response_class=HTMLResponse`.

## Development

```sh
uv sync
uv run pytest
uv run ruff check .
uv run ty check
```
