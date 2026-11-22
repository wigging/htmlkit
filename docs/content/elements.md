# Elements and content

Use `class_`, `input_`, `map_`, `object_`, and `del_` for the corresponding HTML tags that conflict with reserved Python objects; svg and math are not included. For custom tags, import `Element` and use `Element("my-widget", "Text")`. Void elements such as `meta`, `link`, and `input` do not accept children.

Children can be text, integers, elements, fragments, or nested lists and tuples; `None` is ignored. Text and attribute values are escaped automatically: `&`, `<`, `>`, `"`, and `'` become `&amp;`, `&lt;`, `&gt;`, `&#34;`, and `&#39;`, as shown below:

```python
from htmlkit import p

str(p("A < B & C"))
# '<p>A &lt; B &amp; C</p>'

str(p("Note", class_="note", data_id=7))
# '<p class="note" data-id="7">Note</p>'
```

Attributes are keywords, not positional mappings. A trailing underscore is stripped, then internal underscores become hyphens: `class_` becomes `class`, `for_` becomes `for`, `data_id` becomes `data-id`, and `http_equiv` becomes `http-equiv`. Attribute names become lowercase, so `ID` and `id` refer to the same attribute. `True` adds a bare attribute; `False` and `None` omit it. Supplying two keywords that normalize to the same attribute name raises `TypeError`. String, integer, and floating-point attribute values are supported; numbers use Python's `str()` representation, for example `step=0.01` becomes `step="0.01"`. Tag names, attribute names, and executable attribute values must be trusted: escaping is not sanitization.

Render with `str(element)` or `print(element)`. The `html` element adds the HTML5 doctype. Calling an existing element creates a new one, merging attributes and replacing children.

To write attributes before content, as they appear in HTML, set the attributes first and then call the element with its children:

```python
from htmlkit import div, p

ex1 = p(class_="card my-12")("hello there!")
str(ex1)
# '<p class="card my-12">hello there!</p>'

ex2 = div(class_="card")(p("First"), p("Second"))
str(ex2)
# '<div class="card"><p>First</p><p>Second</p></div>'
```

Chaining makes one extra call, so it is slightly slower than passing attributes after the children. To reuse the same attributes, build the element once and call it for each child; its attributes render only once, which is faster than either form:

```python
card = p(class_="card my-12")

str(card("First"))
# '<p class="card my-12">First</p>'

str(card("Second"))
# '<p class="card my-12">Second</p>'
```
