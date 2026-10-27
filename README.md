# htmpy

Efficiently write HTML directly in Python with htmpy. This allows developers to skip Jinja templates and use familiar Python tools like linters, formatters, and debuggers to build web apps more easily.

```python
from htmpy import body, h1, head, html, p, title

page = html(
    head(title("Hello from Python")),
    body(
        h1("Hello from Python", id="banner", style="font-style: italic;"),
        p("Write HTML with htmpy.", class_="intro"),
    ),
    lang="en",
)

print(page)
```

The formatted output is:

```html
<!doctype html>
<html lang="en">
  <head>
    <title>Hello from Python</title>
  </head>
  <body>
    <h1 id="banner" style="font-style: italic">Hello from Python</h1>
    <p class="intro">Write HTML with htmpy.</p>
  </body>
</html>
```

## Installation

Install htmpy with the awesome uv tool. See <https://docs.astral.sh/uv/> for instructions on installing uv and using it to manage Python projects and dependencies.

```sh
uv add htmpy
```

## Documentation

See the htmpy documentation for more information about the package.

## Contributing

Contribute to this project by submitting a pull request or issue. Pull requests should pass all checks and tests before submitting.

```sh
uv sync
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```
