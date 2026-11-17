# Elements and content

Build a page by nesting htmlkit elements. Text is escaped automatically, and
attributes are passed as keyword arguments.

## Text and attributes

```python
from htmlkit import p

paragraph = p("A < B & C", class_="intro")
print(paragraph)
```

The output is:

```html
<p class="intro">A &lt; B &amp; C</p>
```

- Use `class_` for the HTML `class` attribute.
- Use `data_id` for the HTML `data-id` attribute.
- Set an attribute to `True` to include it without a value.
- Set an attribute to `False` or `None` to omit it.

## Lists

Use `repeat()` to create an element for each item:

```python
from htmlkit import li, ul

items = ul(li.repeat(["Apples", "Pears & peaches", "Oranges"]))
print(items)
```

Return to the [documentation home](index.html).

## Blah blah

Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since 1966, when designers at Letraset and James Mosley, the librarian at St Bride Printing Library in London, took a 1914 Cicero translation and scrambled it to make dummy text for Letraset's Body Type sheets. It has survived not only many decades, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised thanks to these sheets and more recently with desktop publishing software like Aldus PageMaker and Microsoft Word including versions of Lorem Ipsum.
