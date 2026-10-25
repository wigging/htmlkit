# htmpy

Write HTML in Python. Requires Python 3.14 or newer; MarkupSafe is the only
runtime dependency.
Pass child elements or text positionally and attributes as keywords.

```python
import htmpy

page = htmpy.html(
    htmpy.head(htmpy.title("Hello from Python")),
    htmpy.body(
        htmpy.h1("Hello from Python"),
        htmpy.p("Write HTML with htmpy.", class_="intro"),
    ),
    lang="en",
)

print(page)
```

Output:

```html
<!doctype html><html lang="en"><head><title>Hello from Python</title></head><body><h1>Hello from Python</h1><p class="intro">Write HTML with htmpy.</p></body></html>
```

## Elements and content

Use `import htmpy`, import individual elements, or use `from htmpy import tags`
and access elements such as `tags.p`. Use `input_`, `map_`, `object_`, and `del_`
for the corresponding HTML tags; `svg` and `math` are not included.
For custom tags, import `Element` and use `Element("my-widget", "Text")`.
Void elements such as `meta`, `link`, and `input` do not accept children.

Children can be text, integers, elements, fragments, or nested lists and tuples.
`None` is ignored. Text and attribute values are escaped automatically, writing
`&amp;`, `&lt;`, `&gt;`, `&#34;`, and `&#39;` as MarkupSafe does:

```python
from htmpy import p

str(p("A < B & C"))
# '<p>A &lt; B &amp; C</p>'

str(p("Note", class_="note", data_id=7))
# '<p class="note" data-id="7">Note</p>'
```

Attributes are keywords, not positional mappings. A trailing underscore is stripped,
then internal underscores become hyphens: `class_` becomes `class`, `for_` becomes
`for`, `data_id` becomes `data-id`, and `http_equiv` becomes `http-equiv`.
Attribute names become lowercase, so `ID` and `id` refer to the same attribute.
`True` adds a bare attribute; `False` and `None` omit it. Supplying two keywords
that normalize to the same attribute name raises `TypeError`.
String, integer, and floating-point attribute values are supported; numbers use
Python's `str()` representation, for example `step=0.01` becomes `step="0.01"`.
Tag names, attribute names, and executable attribute values must be trusted:
escaping is not sanitization.

Render with `str(element)` or `print(element)`. The `html` element adds the HTML5
doctype. Calling an existing element creates a new one, merging attributes and
replacing children.

## Lists and fragments

Use `repeat()` to create one element per item, sharing the same attributes:

```python
from htmpy import ul, li

items = ul(li.repeat(["Apples", "Pears & peaches"]))
row = li(class_="result")
results = ul(row.repeat(["Alice", "Bob"]))
```

`repeat()` returns a `Fragment`. Void elements do not support it unless they
hold placeholders, as described next.

For rows with several values per item, build the element once with `each`
placeholders and let `repeat()` fill them from every item. `each` stands for
the item being rendered: `each.name` reads its `name` attribute, `each[key]`
indexes it, `each(callable)` calls a function with it, and `each` alone is the
item itself. Placeholders are strings, so they also work inside attribute
values and longer strings:

```python
from dataclasses import dataclass

from htmpy import a, each, table, tbody, td, th, thead, tr


@dataclass
class Item:
    name: str
    status: str
    href: str
    archived: bool


items = [
    Item(name="Widget", status="active", href="/items/1", archived=False),
    Item(name="Gizmo", status="paused", href="/items/2", archived=True),
]

row = tr(
    td(each.name, class_="status " + each.status),
    td(a("Edit", href=each.href), hidden=each.archived),
)
page = table(
    thead(tr(th("Name"), th("Action"))),
    tbody(row.repeat(items)),
)
print(page)
```

The output, shown here with line breaks added, fills the template once per
item:

```html
<table>
<thead><tr><th>Name</th><th>Action</th></tr></thead>
<tbody>
<tr><td class="status active">Widget</td><td><a href="/items/1">Edit</a></td></tr>
<tr><td class="status paused">Gizmo</td><td hidden><a href="/items/2">Edit</a></td></tr>
</tbody>
</table>
```

A whole bound attribute follows the usual rules: `None` and `False` omit it,
`True` renders only its name, as `hidden` does above. Bound values are escaped
like children, so an element or a `repeat()` result can be bound to nest
loops. `each("owner.name")` reads a dotted path, and `bind()` is the function
behind `each` for code that prefers it. A template's HTML is compiled on its
first `repeat()`, so rows cost far less than building each element; an element
with placeholders is meant for `repeat()`, and rendering it directly leaves the
placeholders in the output.

Use `Fragment` to group children without a wrapping tag, or `from_iterable()`
to collect a generator:

```python
from htmpy import Fragment, h1, p

content = Fragment(h1("Welcome"), p("A & B"))
paragraphs = Fragment.from_iterable(p(name) for name in ["Alice", "Bob"])
```

Both `repeat()` and `from_iterable()` consume their input immediately.

## Trusted HTML

Use `Raw` for trusted markup that must not be escaped, such as scripts and styles:

```python
from htmpy import Raw, head, script, style

head(
    style(Raw("body > main { margin: 0 auto }")),
    script(Raw("if (a < b && c) { go(); }")),
)
```

`Raw` is not sanitized. Child objects with an `__html__()` method also bypass
escaping. Elements, fragments, and `Raw` support this protocol for use with
MarkupSafe, Jinja, and Django.

Pass elements, fragments, and `Raw` directly as children. Converting them to
`str` first causes their HTML to be escaped again.

## FastAPI example

Install FastAPI separately and pass an element directly to `HTMLResponse`:

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

Return `HTMLResponse`, not a bare element, to avoid JSON serialization.

## Development

```sh
uv sync
uv run pytest
uv run ruff check .
uv run ty check
```
