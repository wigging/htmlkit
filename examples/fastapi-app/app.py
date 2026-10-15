"""A simple web app example that returns a basic HTML web page."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from page import basic_page

app = FastAPI()


@app.get("/")
async def web_page():
    """Return the content of the HTML page."""
    page = basic_page()
    return HTMLResponse(page)
