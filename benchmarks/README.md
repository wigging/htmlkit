# Simple page benchmark

Run from the project root:

```sh
uv run benchmarks/simple_page.py
```

The benchmark creates the same HTML document with htmpy and Jinja: a head
containing a UTF-8 charset meta element and a stylesheet link, followed by a
heading and paragraph, with a language attribute and paragraph class. Both
implementations escape dynamic text and return a complete HTML string. The
script checks all three outputs against the expected HTML before timing.

The benchmark reports three paths:

- **htmpy fresh** constructs every element and attribute dictionary on each iteration.
- **htmpy reused** prepares the static head and the HTML and paragraph attribute
  templates once. Each iteration constructs fresh dynamic elements, escapes the
  heading and message, and renders a complete page. It uses the existing immutable
  element API; it does not cache completed pages or dynamic text.
- **Jinja** reuses a template compiled once outside the timed section.

The reused htmpy path and Jinja both exclude static preparation, as applications
can do when reusing templates. The fresh htmpy path is retained to show the cost
of rebuilding everything. Imports, preparation, validation, and printing are
excluded from the timings; there is no file or network I/O.

Results report the median time per page across five repeats of 10,000 pages
using Python's `timeit` (which disables garbage collection during timing).
Lower is faster. Timings depend on the machine and Python version; this small
page is not representative of every workload.

Jinja is a development dependency, not an htmpy runtime dependency.

## Unordered list benchmark

```sh
uv run benchmarks/unordered_list.py
```

Creates an unordered list with 1,000 list items. The htmpy path uses a Python
list comprehension to construct fresh `li` elements and passes them to `ul`; the Jinja
path uses a template for-loop over the same input strings. Both return complete
HTML strings and escape dynamic text containing `&` and angle brackets.
The script checks both outputs against independently constructed expected HTML
before timing.

Like the simple page benchmark, this reports median time using five `timeit`
repeats, with input preparation, Jinja compilation, validation, and printing
excluded. Each repeat renders 1,000 lists rather than 10,000 pages to keep the
larger workload practical. Results are in microseconds per complete list, not
per item. There is no separate htmpy reused path because the bare `ul` and `li`
elements already serve as reusable templates; no static subtrees or attribute
dictionaries need preparation.
