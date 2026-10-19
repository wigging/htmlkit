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

Creates an unordered list with 1,000 list items. The original htmpy path uses a Python
list comprehension to construct fresh `li` elements and passes them to `ul`.
The **htmpy repeat** path uses `ul(li.repeat(items))`, avoiding intermediate element
objects. The Jinja path uses a template for-loop over the same input strings.
All three return complete
HTML strings and escape dynamic text containing `&` and angle brackets.
The script checks all three outputs against independently constructed expected HTML
before timing.

Like the simple page benchmark, this reports median time using five `timeit`
repeats, with input preparation, Jinja compilation, validation, and printing
excluded. Each repeat renders 1,000 lists rather than 10,000 pages to keep the
larger workload practical. Results are in microseconds per complete list, not
per item. There is no separate htmpy reused path because the bare `ul` and `li`
elements already serve as reusable templates; no static subtrees or attribute
dictionaries need preparation.

## Fragment benchmark

```sh
uv run benchmarks/fragments.py
```

Compares `Fragment(*children)`, `Fragment.from_iterable(children)`, and compiled,
autoescaped Jinja templates for two workloads without a wrapping element:

- A small fragment with a heading, separator text, and paragraph.
- A fragment containing 1,000 generated paragraphs.

The small iterable case uses a tuple. The two large constructor cases generate fresh `p`
elements: `Fragment` expands a generator into positional arguments, while
`from_iterable` consumes a generator directly. Element construction, escaping,
and rendering the final string are included in the timings. No rendered children
are cached. Input strings and Jinja templates are prepared outside the timings.
This measures complete rendering paths, not isolated fragment-wrapper overhead.

The large workload also includes `p.repeat(ITEMS)`, which returns a fragment
without allocating an element for each paragraph. It reuses the paragraph's
opening and closing tags while still escaping every input string. The mixed-tag
small workload has no equivalent single-tag `repeat()` case.

Before timing, all outputs for each workload must equal independently
constructed expected HTML, including escaped ampersands and angle brackets.
The script reports median microseconds per complete fragment across five repeats
of 10,000 small fragments or 1,000 large fragments. As with the other benchmarks,
`timeit` disables garbage collection, and results depend on the machine and Python
version. These are eager renders, not streaming or peak-memory measurements.

## Deep nesting benchmark

```sh
uv run benchmarks/nested.py
```

Builds a fresh paragraph inside 10, 100, 1,000, and 5,000 nested `div` elements,
using both a short text payload and a payload 256 times larger. Each render
includes escaping the paragraph text, constructing every wrapper, and returning
the complete HTML string. An iterative loop avoids measuring Python's recursion
limit. No intermediate elements are retained after their parent is constructed.

The Jinja path uses a compiled, autoescaped template with loops that emit the
opening wrappers, the escaped paragraph, and the closing wrappers. It produces
the same nested HTML without recursive macros or repeated subtree construction.
This compares complete output generation, not equivalent component-call trees.
Template compilation is excluded from both time and memory measurements, as in
the other benchmarks; no completed output is cached.

Every case is checked against independently assembled expected HTML, including
escaped ampersands and angle brackets, before timing. Input preparation and
validation are excluded. The output reports UTF-8 output size and median time
across five repeats of 100 renders, with `timeit` disabling garbage collection.
Each depth and payload combination reports both htmpy and Jinja results.

Peak memory is measured separately with `tracemalloc`, using the median of five
single renders and a fresh tracing session for each sample. The final string
remains alive when the peak is read. Tracing is disabled during timing, and
inputs and expected strings are allocated before tracing starts. The reported
peak covers traced Python allocations, not process RSS or total bytes allocated
over the render's lifetime.

In htmpy, each parent copies its child's rendered HTML. For a chain of depth d and escaped
payload length n, this entails O(d² + d·n) cumulative character copying, while
peak live string storage can remain O(d + n) when intermediate elements are
released. Retaining all intermediate elements would be a different memory
workload. Use the depth and payload sweeps to evaluate future rendering changes;
these synthetic depths are stress cases, not browser-layout benchmarks or a
reason on their own to replace eager rendering. Results depend on the machine
and Python version.
