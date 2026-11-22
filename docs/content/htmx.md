# htmx syntax

The htmlkit package works with [htmx 2](https://v2.htmx.org/docs/) through ordinary HTML attributes; no adapter is needed. The `examples/fastapi-htmx/` app uses htmx 2.0.11 with a pinned CDN URL and integrity hash. Run it from the repository root:

```bash
uv run fastapi dev examples/fastapi-htmx/app.py
```

With the htmx script loaded, a button can request an HTML fragment and swap it into a target:

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from htmlkit import Fragment, button, div, p

app = FastAPI()

content = Fragment(
    button("Get a quote", hx_get="/quotes", hx_target="#quote", hx_swap="innerHTML"),
    div(id="quote"),
)


@app.get("/quotes", response_class=HTMLResponse)
def quotes():
    return HTMLResponse(Fragment(p("He who is brave is free."), p("~ Seneca")))
```

All htmx attribute names follow htmlkit's normal rules: `hx_get` becomes `hx-get`, `hx_select_oob` becomes `hx-select-oob`, and `data_hx_get` becomes `data-hx-get`. Values retain their case, including `innerHTML` and `outerHTML`. Render partial responses with `Element` or `Fragment`, rather than wrapping them in `html`.

## Boolean and JSON values

Use strings for htmx options that require a value: `hx_boost="true"`, `hx_push_url="false"`, `hx_history="false"`, and `hx_validate="true"`. Python `True` renders a bare attribute and `False` omits it; they do not produce the strings `"true"` and `"false"`. Omitting an inherited option does not disable it. Presence-only attributes such as `hx_disable`, `hx_preserve`, and `hx_history_elt` can use `True`.

Serialize `hx_vals`, `hx_headers`, and `hx_request` with `json.dumps()`. htmlkit escapes the attribute value, and the browser decodes it before htmx parses the JSON. Do not pre-escape it or wrap it in `Raw`.

```python
import json

save = button(
    "Save",
    hx_post="/items",
    hx_vals=json.dumps({"label": "A & B", "enabled": False}),
    hx_push_url="false",
)
```

## Event handlers

htmx 2 uses `hx-on:*` event attributes rather than the removed htmx 1 `hx-on` syntax. For names containing colons, such as `hx-on:click`, use dictionary unpacking because colons cannot appear in Python keyword arguments:

```python
from htmlkit import button

click = button("Click me", **{"hx-on:click": "alert('Clicked!')"})
```

This renders:

```html
<button hx-on:click="alert(&#39;Clicked!&#39;)">Click me</button>
```

The browser decodes the escaped quotes before htmx executes the handler. htmx 2 also supports a dash equivalent, which works with htmlkit's underscore-to-hyphen conversion:

```python
click = button("Click me", hx_on_click="alert('Clicked!')")
# Renders hx-on-click="...", equivalent to hx-on:click="...".
```

For htmx lifecycle events, `hx_on__before_request` becomes `hx-on--before-request`, equivalent to `hx-on::before-request` (note the double underscore). Both forms can be used together:

```python
load = button(
    "Load",
    hx_get="/quotes",
    hx_target="#quote",
    hx_on__before_request="this.classList.add('loading')",
    **{"hx-on::after-request": "this.classList.remove('loading')"},
)
```

Use kebab-case event names (`before-request`, not `beforeRequest`), because HTML attribute names are lowercase. Handler scripts must be trusted application code; escaping does not make user-supplied JavaScript safe.
