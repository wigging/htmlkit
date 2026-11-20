<p align="center">
  <img src="https://raw.githubusercontent.com/wigging/htmlkit/main/assets/icon.webp" alt="htmlkit icon with cyan and magenta angle brackets" width="200" height="200">
</p>

<h1 align="center">htmlkit</h1>

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

```bash
uv add htmlkit
```

Or with pip:

```bash
pip install htmlkit
```

Or install the development version directly from GitHub:

```bash
uv add git+https://github.com/wigging/htmlkit
```

## Documentation

The online documentation at [gavinw.me/htmlkit](https://gavinw.me/htmlkit/) covers elements and attributes, lists and fragments, trusted HTML, and using htmlkit with FastAPI.

The documentation is written as Markdown files in the `docs/content/` directory. The `docs/build.py` script renders them into HTML pages in `docs/` using the layout in `docs/layout.py`. Build the documentation locally with:

```bash
uv run docs/build.py
```

## Contributing

Contribute to this project by submitting a pull request or issue. Pull requests should pass all checks and tests before submitting.

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```
