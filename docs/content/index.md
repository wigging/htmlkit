# htmlkit

Write HTML in Python with familiar objects instead of templates.

## Installation

Requires Python 3.14 or newer. Install htmlkit with uv as shown below:

```bash
uv add htmlkit
```

## Getting started

```python
from htmlkit import body, h1, html, p

page = html(body(h1("Hello"), p("Built with htmlkit.")))
print(page)
```

Read [Elements and content](elements.html) for more examples.

## Building these docs

The documentation content lives in `docs/content/` as Markdown files. Run this
command from the repository root:

```bash
uv run docs/build.py
```

Each Markdown file becomes an HTML page in `docs/`, using the shared htmlkit
layout. Open `docs/index.html` in your browser to view the result.
