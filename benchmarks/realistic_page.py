"""Compare a realistic page with navigation, a data table, and a form against Jinja."""

from statistics import median
from timeit import repeat
from typing import NamedTuple

from jinja2 import Environment

from htmlkit import (
    a,
    body,
    button,
    each,
    footer,
    form,
    h1,
    h2,
    head,
    header,
    html,
    input_,
    label,
    li,
    link,
    meta,
    nav,
    option,
    p,
    section,
    select,
    table,
    tags,
    tbody,
    td,
    textarea,
    th,
    thead,
    time,
    title,
    tr,
    ul,
)

ROW_COUNT = 50
NAVIGATION = (
    ("/", "Home"),
    ("/items", "Items & stock"),
    ("/orders", "Orders"),
    ("/reports", "Reports"),
    ("/settings", "Settings"),
)
COLUMNS = ("ID", "Name", "Owner", "Quantity", "Status", "Actions")
FIELDS = (
    ("name", "Name", "text", "Gadget & <Co>"),
    ("sku", "SKU", "text", "GX-200"),
    ("owner", "Owner", "text", "Zoë"),
    ("quantity", "Quantity", "number", "12"),
    ("location", "Location", "text", "Aisle 4 <bay 2>"),
    ("supplier", "Supplier", "text", "Smith & Sons"),
    ("email", "Supplier email", "email", "orders@example.com"),
    ("cost", "Unit cost", "number", "19.99"),
    ("reorder", "Reorder level", "number", "5"),
    ("tags", "Tags", "text", "hardware, café"),
)
PRIORITIES = ("low", "normal", "high")
PRIORITY = "normal"
PAGE_TITLE = "Inventory & stock"
CURRENT = "/items"
NOTES = "Restock <soon> & verify."
UPDATED = "2026-10-19T09:30:00Z"
UPDATED_LABEL = "19 October 2026"


class Row(NamedTuple):
    """One inventory table row."""

    id: int
    name: str
    owner: str
    quantity: int
    status: str
    href: str


ROWS = [
    Row(
        index,
        f"Widget {index} & <parts>",
        "José" if index % 3 else "Zoë",
        index * 7 % 50,
        "active" if index % 4 else "paused",
        f"/items/{index}?tab=edit&from=list",
    )
    for index in range(1, ROW_COUNT + 1)
]
CONTEXT = {
    "title": PAGE_TITLE,
    "current": CURRENT,
    "navigation": NAVIGATION,
    "columns": COLUMNS,
    "rows": ROWS,
    "fields": FIELDS,
    "priorities": PRIORITIES,
    "priority": PRIORITY,
    "notes": NOTES,
    "updated": UPDATED,
    "updated_label": UPDATED_LABEL,
}
TEMPLATE = Environment(autoescape=True).from_string(
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{{ title }}</title>'
    '<link rel="stylesheet" href="/styles.css"></head><body><header><nav><ul>'
    '{% for href, text in navigation %}<li><a href="{{ href }}"'
    '{% if href == current %} class="active"{% endif %}>{{ text }}</a></li>{% endfor %}'
    "</ul></nav><h1>{{ title }}</h1></header>"
    '<main><section id="inventory"><h2>{{ rows|length }} items</h2><table class="data"><thead><tr>'
    '{% for column in columns %}<th scope="col">{{ column }}</th>{% endfor %}</tr></thead><tbody>'
    "{% for row in rows %}<tr><td>{{ row.id }}</td><td>{{ row.name }}</td><td>{{ row.owner }}</td>"
    '<td class="number">{{ row.quantity }}</td>'
    '<td class="status {{ row.status }}">{{ row.status }}</td>'
    '<td><a href="{{ row.href }}">Edit</a></td></tr>{% endfor %}</tbody></table></section>'
    '<section id="new-item"><h2>Add item</h2><form method="post" action="/items">'
    '{% for name, text, kind, value in fields %}<label for="{{ name }}">{{ text }}</label>'
    '<input type="{{ kind }}" id="{{ name }}" name="{{ name }}" value="{{ value }}" required>'
    '{% endfor %}<label for="priority">Priority</label><select id="priority" name="priority">'
    '{% for value in priorities %}<option value="{{ value }}"'
    "{% if value == priority %} selected{% endif %}>{{ value|capitalize }}</option>{% endfor %}"
    '</select><label for="notes">Notes</label>'
    '<textarea id="notes" name="notes" rows="4">{{ notes }}</textarea>'
    '<button type="submit" class="primary">Save &amp; close</button></form></section></main>'
    '<footer><p>Updated <time datetime="{{ updated }}">{{ updated_label }}</time></p></footer>'
    "</body></html>"
)
NUMBER = 1_000
REPEAT = 5

# Static parts prepared once for the reused htmlkit renderer.
HEAD = head(
    meta(charset="utf-8"),
    title(PAGE_TITLE),
    link(rel="stylesheet", href="/styles.css"),
)
HEADER = header(
    nav(
        ul(
            [
                li(
                    a(
                        text,
                        href=href,
                        class_="active" if href == CURRENT else None,
                    )
                )
                for href, text in NAVIGATION
            ]
        )
    ),
    h1(PAGE_TITLE),
)
TABLE_HEAD = thead(tr([th(column, scope="col") for column in COLUMNS]))
FORM_TAIL = (
    label("Notes", for_="notes"),
    textarea(NOTES, id="notes", name="notes", rows=4),
    button("Save & close", type="submit", class_="primary"),
)
FOOTER = footer(p("Updated ", time(UPDATED_LABEL, datetime=UPDATED)))
PAGE = html(lang="en")
DATA_TABLE = table(class_="data")
NUMBER_CELL = td(class_="number")
ITEM_FORM = form(method="post", action="/items")
PRIORITY_SELECT = select(id="priority", name="priority")
# A row template filled by repeat(), prepared once like the Jinja template.
ROW = tr(
    td(each.id),
    td(each.name),
    td(each.owner),
    NUMBER_CELL(each.quantity),
    td(each.status, class_="status " + each.status),
    td(a("Edit", href=each.href)),
)


def render_htmlkit_fresh() -> str:
    """Render the page by building every element on each call."""
    current = CURRENT
    priority = PRIORITY
    rows = ROWS
    page = html(
        head(
            meta(charset="utf-8"),
            title(PAGE_TITLE),
            link(rel="stylesheet", href="/styles.css"),
        ),
        body(
            header(
                nav(
                    ul(
                        [
                            li(
                                a(
                                    text,
                                    href=href,
                                    class_="active" if href == current else None,
                                )
                            )
                            for href, text in NAVIGATION
                        ]
                    )
                ),
                h1(PAGE_TITLE),
            ),
            tags.main(
                section(
                    h2(len(rows), " items"),
                    table(
                        thead(tr([th(column, scope="col") for column in COLUMNS])),
                        tbody(
                            [
                                tr(
                                    td(row.id),
                                    td(row.name),
                                    td(row.owner),
                                    td(row.quantity, class_="number"),
                                    td(row.status, class_="status " + row.status),
                                    td(a("Edit", href=row.href)),
                                )
                                for row in rows
                            ]
                        ),
                        class_="data",
                    ),
                    id="inventory",
                ),
                section(
                    h2("Add item"),
                    form(
                        [
                            (
                                label(text, for_=name),
                                input_(
                                    type=kind,
                                    id=name,
                                    name=name,
                                    value=value,
                                    required=True,
                                ),
                            )
                            for name, text, kind, value in FIELDS
                        ],
                        label("Priority", for_="priority"),
                        select(
                            [
                                option(
                                    value.capitalize(),
                                    value=value,
                                    selected=value == priority,
                                )
                                for value in PRIORITIES
                            ],
                            id="priority",
                            name="priority",
                        ),
                        label("Notes", for_="notes"),
                        textarea(NOTES, id="notes", name="notes", rows=4),
                        button("Save & close", type="submit", class_="primary"),
                        method="post",
                        action="/items",
                    ),
                    id="new-item",
                ),
            ),
            footer(p("Updated ", time(UPDATED_LABEL, datetime=UPDATED))),
        ),
        lang="en",
    )
    return str(page)


def render_htmlkit_reused() -> str:
    """Render the page with prepared static sections and attributed templates."""
    priority = PRIORITY
    rows = ROWS
    page = PAGE(
        HEAD,
        body(
            HEADER,
            tags.main(
                section(
                    h2(len(rows), " items"),
                    DATA_TABLE(
                        TABLE_HEAD,
                        tbody(
                            [
                                tr(
                                    td(row.id),
                                    td(row.name),
                                    td(row.owner),
                                    NUMBER_CELL(row.quantity),
                                    td(row.status, class_="status " + row.status),
                                    td(a("Edit", href=row.href)),
                                )
                                for row in rows
                            ]
                        ),
                    ),
                    id="inventory",
                ),
                section(
                    h2("Add item"),
                    ITEM_FORM(
                        [
                            (
                                label(text, for_=name),
                                input_(
                                    type=kind,
                                    id=name,
                                    name=name,
                                    value=value,
                                    required=True,
                                ),
                            )
                            for name, text, kind, value in FIELDS
                        ],
                        label("Priority", for_="priority"),
                        PRIORITY_SELECT(
                            [
                                option(
                                    value.capitalize(),
                                    value=value,
                                    selected=value == priority,
                                )
                                for value in PRIORITIES
                            ]
                        ),
                        FORM_TAIL,
                    ),
                    id="new-item",
                ),
            ),
            FOOTER,
        ),
    )
    return str(page)


def render_htmlkit_repeat() -> str:
    """Render the reused page with the table rows filled from a row template."""
    priority = PRIORITY
    rows = ROWS
    page = PAGE(
        HEAD,
        body(
            HEADER,
            tags.main(
                section(
                    h2(len(rows), " items"),
                    DATA_TABLE(
                        TABLE_HEAD,
                        tbody(ROW.repeat(rows)),
                    ),
                    id="inventory",
                ),
                section(
                    h2("Add item"),
                    ITEM_FORM(
                        [
                            (
                                label(text, for_=name),
                                input_(
                                    type=kind,
                                    id=name,
                                    name=name,
                                    value=value,
                                    required=True,
                                ),
                            )
                            for name, text, kind, value in FIELDS
                        ],
                        label("Priority", for_="priority"),
                        PRIORITY_SELECT(
                            [
                                option(
                                    value.capitalize(),
                                    value=value,
                                    selected=value == priority,
                                )
                                for value in PRIORITIES
                            ]
                        ),
                        FORM_TAIL,
                    ),
                    id="new-item",
                ),
            ),
            FOOTER,
        ),
    )
    return str(page)


def render_jinja() -> str:
    """Render the page using the compiled Jinja template."""
    return TEMPLATE.render(CONTEXT)


def _expected() -> str:
    """Assemble the expected page from the context with hand-escaped text."""
    navigation = "".join(
        f'<li><a href="{href}"{' class="active"' if href == "/items" else ""}>'
        f"{text.replace('&', '&amp;')}</a></li>"
        for href, text in NAVIGATION
    )
    columns = "".join(f'<th scope="col">{column}</th>' for column in COLUMNS)
    rows = "".join(
        f"<tr><td>{index}</td><td>Widget {index} &amp; &lt;parts&gt;</td>"
        f"<td>{'José' if index % 3 else 'Zoë'}</td>"
        f'<td class="number">{index * 7 % 50}</td>'
        f'<td class="status {"active" if index % 4 else "paused"}">'
        f"{'active' if index % 4 else 'paused'}</td>"
        f'<td><a href="/items/{index}?tab=edit&amp;from=list">Edit</a></td></tr>'
        for index in range(1, ROW_COUNT + 1)
    )
    escaped_values = {
        "name": "Gadget &amp; &lt;Co&gt;",
        "location": "Aisle 4 &lt;bay 2&gt;",
        "supplier": "Smith &amp; Sons",
    }
    fields = "".join(
        f'<label for="{name}">{text}</label>'
        f'<input type="{kind}" id="{name}" name="{name}" '
        f'value="{escaped_values.get(name, value)}" required>'
        for name, text, kind, value in FIELDS
    )
    options = "".join(
        f'<option value="{value}"{" selected" if value == "normal" else ""}>'
        f"{value.capitalize()}</option>"
        for value in PRIORITIES
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        "<title>Inventory &amp; stock</title>"
        '<link rel="stylesheet" href="/styles.css"></head><body>'
        f"<header><nav><ul>{navigation}</ul></nav><h1>Inventory &amp; stock</h1></header>"
        f'<main><section id="inventory"><h2>{ROW_COUNT} items</h2><table class="data">'
        f"<thead><tr>{columns}</tr></thead><tbody>{rows}</tbody></table></section>"
        '<section id="new-item"><h2>Add item</h2><form method="post" action="/items">'
        f'{fields}<label for="priority">Priority</label>'
        f'<select id="priority" name="priority">{options}</select>'
        '<label for="notes">Notes</label>'
        '<textarea id="notes" name="notes" rows="4">Restock &lt;soon&gt; &amp; verify.</textarea>'
        '<button type="submit" class="primary">Save &amp; close</button></form></section></main>'
        '<footer><p>Updated <time datetime="2026-10-19T09:30:00Z">19 October 2026</time></p>'
        "</footer></body></html>"
    )


def main() -> None:
    """Validate page output and report median rendering times."""
    expected = _expected()
    assert render_htmlkit_fresh() == render_htmlkit_reused() == render_jinja() == expected
    assert render_htmlkit_repeat() == expected

    print(
        f"{REPEAT} repeats of {NUMBER:,} pages with a {ROW_COUNT}-row table and "
        f"{len(FIELDS) + 2}-field form ({len(expected.encode()):,} bytes); median time per page"
    )
    print("Input preparation and Jinja compilation excluded; autoescaping enabled.")
    for name, render in (
        ("htmlkit fresh", render_htmlkit_fresh),
        ("htmlkit reused", render_htmlkit_reused),
        ("htmlkit repeat", render_htmlkit_repeat),
        ("Jinja", render_jinja),
    ):
        seconds = median(repeat(render, number=NUMBER, repeat=REPEAT)) / NUMBER
        print(f"{name:12}: {seconds * 1_000_000:9.2f} µs/page")


if __name__ == "__main__":
    main()
