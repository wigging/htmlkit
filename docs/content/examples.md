# Code examples

The repository's [examples](https://github.com/wigging/htmlkit/tree/main/examples) directory shows how to use htmlkit to build static websites and serve HTML from FastAPI. Each example is discussed below.

## bootstrap-site

The [build.py](https://github.com/wigging/htmlkit/blob/main/examples/bootstrap-site/build.py) generates Home and About pages from a shared layout styled with Bootstrap 6. Both pages have a responsive sidebar that highlights the current page.

## fastapi-app

The [app.py](https://github.com/wigging/htmlkit/blob/main/examples/fastapi-app/app.py) serves a complete HTML document at `/`. It calls `basic_page()` to build the page with htmlkit and passes the resulting element directly to a FastAPI `HTMLResponse`.

## fastapi-htmx

Clicking **Get a quote** sends an htmx request to the [/quotes](https://github.com/wigging/htmlkit/blob/main/examples/fastapi-htmx/app.py) route. FastAPI returns a random quote and its author as an htmlkit `Fragment`, and htmx updates just the quote without reloading the page.

## static-site

The [build.py](https://github.com/wigging/htmlkit/blob/main/examples/static-site/build.py) writes two linked files, `index.html` and `page.html`. Each page supplies its content as a `Fragment` to a shared layout that loads a local stylesheet. The index includes a syntax-highlighted Python example.
