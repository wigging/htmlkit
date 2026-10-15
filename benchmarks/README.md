# Simple page benchmark

Run from the project root:

```sh
uv run benchmarks/simple_page.py
```

The benchmark creates the same HTML document with htmpy and Jinja: a head,
heading, and paragraph, with a language attribute and paragraph class. Both
implementations escape dynamic text and return a complete HTML string. The
script checks both outputs against the expected HTML before timing.

Jinja's template is compiled once outside the timed section, as it would be
when reusing a cached template. Each htmpy iteration constructs fresh elements
and converts the page to a string. Imports, template compilation, validation,
and printing are excluded from the timings; there is no file or network I/O.

Results report the median time per page across five repeats of 10,000 pages
using Python's `timeit` (which disables garbage collection during timing).
Lower is faster. Timings depend on the machine and Python version; this small
page is not representative of every workload.

Jinja is a development dependency, not an htmpy runtime dependency.
