# Lists and fragments

Use `repeat()` to create one element per item, sharing the same attributes:

```python
from htmlkit import ul, li

items = ul(li.repeat(["Apples", "Pears & peaches"]))

row = li(class_="result")
results = ul(row.repeat(["Alice", "Bob"]))
```

Note that `repeat()` returns a `Fragment` and void elements do not support it unless they hold placeholders, as described next.

For rows with several values per item, build the element once with `each` placeholders and let `repeat()` fill them from every item. `each` stands for the item being rendered: `each.name` reads its name attribute, `each[key]` indexes it, `each(callable)` calls a function with it, and `each` alone is the item itself. Placeholders are string subclasses that retain their accessors. Use them directly as children or attribute values, or combine them with `+`:

```python
from dataclasses import dataclass

from htmlkit import a, each, table, tbody, td, th, thead, tr


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

The print output, shown here with formatting added, fills the template once per item:

```html
<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Action</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="status active">Widget</td>
      <td><a href="/items/1">Edit</a></td>
    </tr>
    <tr>
      <td class="status paused">Gizmo</td>
      <td hidden><a href="/items/2">Edit</a></td>
    </tr>
  </tbody>
</table>
```

A whole bound attribute follows the usual rules: `None` and `False` omit it, and `True` renders only its name, as hidden does above. Bound values are escaped like children, so an element or a `repeat()` result can be bound to nest loops. `each("owner.name")` reads a dotted path, and `bind()` is the function behind `each` for code that prefers it. A template's HTML is compiled on its first `repeat()`, so rows cost far less than building each element; an element with placeholders is meant for `repeat()`, and rendering it directly leaves the placeholders in the output.

Placeholders and templates keep their callbacks alive for reuse. Once they are discarded, htmlkit no longer retains the callbacks or their captured objects; completed `repeat()` results do not retain them. Use `+` rather than f-strings, `str.join()`, or other operations that discard the string subclass and its accessor references. `repeat()` raises `ValueError` if a placeholder has lost its accessor reference. Alternatively, put string formatting inside a callback, such as `each(lambda item: f"status {item.status}")`.

Use `Fragment` to group children without a wrapping tag, or `from_iterable()` to collect a generator:

```python
from htmlkit import Fragment, h1, p

content = Fragment(h1("Welcome"), p("A & B"))
paragraphs = Fragment.from_iterable(p(name) for name in ["Alice", "Bob"])
```

Both `repeat()` and `from_iterable()` consume their input immediately.
