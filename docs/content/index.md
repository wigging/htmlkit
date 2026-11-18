# htmlkit

Write HTML in Python.

The htmlkit package allows developers to skip Jinja templates and use familiar Python tools like linters, formatters, and debuggers to build web apps more easily.

```python
from htmlkit import body, h1, head, html, p, title

page = html(
    head(title("Hello from Python")),
    body(
        h1("Hello from Python", id="banner", style="font-style: italic;"),
        p("Write HTML in Python with htmlkit.", class_="intro"),
    ),
    lang="en",
)

print(page)
```

The output, formatted here for readability, is:

```html
<!doctype html>
<html lang="en">
  <head>
    <title>Hello from Python</title>
  </head>
  <body>
    <h1 id="banner" style="font-style: italic">Hello from Python</h1>
    <p class="intro">Write HTML in Python with htmlkit.</p>
  </body>
</html>
```

## Installation

Requires Python 3.14 or newer.

Install htmlkit with the awesome [uv](https://docs.astral.sh/uv/) package manager:

```sh
uv add htmlkit
```

Or with pip:

```sh
pip install htmlkit
```

Or install the development version directly from GitHub:

```sh
uv add git+https://github.com/wigging/htmlkit
```

Read [Elements and content](elements.html) to learn more.

## Building these docs

The documentation content lives in `docs/content/` as Markdown files. Run this
command from the repository root:

```bash
uv run docs/build.py
```

Each Markdown file becomes an HTML page in `docs/`, using the shared htmlkit
layout. Open `docs/index.html` in your browser to view the result.
