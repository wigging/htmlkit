# FastAPI web app

In a FastAPI web application, use htmlkit instead of Jinja templates for HTML responses. An htmlkit element can be passed directly to the `HTMLResponse` as demonstrated below.

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from htmlkit import html, body, h1, p

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index():
    page = html(body(h1("Hello"), p("Built with htmlkit.")))
    return HTMLResponse(page)
```

For dynamic updates without a full page reload, see [htmx 2](htmx.html).
