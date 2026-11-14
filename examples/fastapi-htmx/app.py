"""Web app that uses htmx to trigger a GET response for random quotes.

Run with the following command:
uv run fastapi dev examples/fastapi-htmx/app.py
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from index import index_page
from quotes import random_quote

app = FastAPI()


@app.get("/styles.css", response_class=FileResponse)
async def stylesheet() -> FileResponse:
    """Return the example stylesheet."""
    return FileResponse(Path(__file__).with_name("styles.css"), media_type="text/css")


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Return the index page."""
    return HTMLResponse(index_page())


@app.get("/quotes", response_class=HTMLResponse)
async def quotes() -> HTMLResponse:
    """Return a random quote as an HTML fragment."""
    return HTMLResponse(random_quote())
