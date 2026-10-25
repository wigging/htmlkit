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

- **htmpy fresh** constructs every element with keyword attributes on each iteration.
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
values need preparation.

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

Builds a fresh paragraph inside 10, 32, and 100 nested wrappers, using
both a short text payload and a payload 256 times larger. Four shapes are measured:

- Identical bare `div` wrappers, preserving the original baseline.
- Alternating bare `div` and `section` wrappers.
- Alternating wrappers with a fresh `data-level` attribute at every level.
- Alternating wrappers with a trailing `span` containing the level number.

Levels count outward from zero around the paragraph. Attributes and siblings
are separate cases so their costs can be distinguished. Each render includes
escaping the paragraph text, constructing every wrapper, and returning the
complete HTML string. No intermediate elements are retained after their parent
is constructed. Real documents rarely nest deeper than 32 elements, the depth
Lighthouse flags as excessive, so 100 is a stress case rather than a target.

The Jinja path uses a compiled, autoescaped template with loops that emit the
opening wrappers, the escaped paragraph, and the closing wrappers. The mixed
template also selects alternating tags and emits attributes or siblings as needed.
It produces the same nested HTML without recursive macros or repeated subtree
construction.
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

When an element wraps a single element with the same tag, or wraps such a run,
htmpy stores a reference to the child and a run count instead of copying the
child's rendered HTML, then renders the chain once when the HTML is first read.
The identical-tag chain of depth d around an escaped payload of length n costs
O(d + n) copying and live storage, rather than O(d² + d·n) copying. Wrapping a
single element with a different tag, such as `li(a(...))`, copies eagerly,
because that is cheaper than materializing a one-level chain later. The mixed
cases do not start an identical-tag run, so they expose repeated copying of
the growing subtree. Peak live memory does not measure cumulative copying.
For the identical-tag baseline, the remaining per-level cost is one Python call
and one object allocation,
which is the floor for this API: on CPython 3.14 that is about 0.1 µs per
level, while Jinja's compiled loop emits each wrapper in about 0.05 µs. htmpy
therefore wins at depths typical of real documents, where its fixed cost is
lower, and trails Jinja as depth grows. Retaining all intermediate elements
would be a different memory workload. Results depend on the machine and Python
version.

## Realistic page benchmark

```sh
uv run benchmarks/realistic_page.py
```

Builds a complete inventory page of about 12 KB: a head with charset, title,
and stylesheet; a header with a five-link navigation list whose current link
carries an `active` class and a heading; a main section with a 50-row, 6-column
data table whose cells mix integers, escaped names, non-ASCII owners, a status
class attribute, and an edit link with `&` in its URL; a form with ten
label and input pairs using the boolean `required` attribute, a select with a
conditionally `selected` option, a textarea, and a submit button; and a footer
with a `time` element. The page has about 430 elements and 370 escaped values,
so element construction dominates rather than any single long string.

The **htmpy fresh** path builds every element with keyword attributes on each
render. The **htmpy reused** path prepares the static head, header, table head,
footer, and attributed `html`, `table`, `td`, `form`, and `select` templates
once, then builds the table body and form fields on each render. The **Jinja**
path renders one compiled, autoescaped template with `for` loops and `if`
conditions for the same context. Conditional attributes use `None` values in
htmpy, which omit the attribute, and `{% if %}` blocks in Jinja. All three
outputs must equal independently assembled expected HTML before timing.

Results report the median time per page across five repeats of 1,000 pages,
with input preparation, Jinja compilation, validation, and printing excluded.
Every htmpy element costs one Python call and one allocation, so pages with
hundreds of small elements, such as table cells, are where a compiled template
that emits static text in bulk has its largest advantage. Keyword attributes
add to that: each attributed element normalizes its names through a cached
lookup, renders the values, and allocates a new tag definition, which costs
roughly three times as much as an element with only text. Preparing attributed
elements once, as the reused path does with `td(class_="number")`, pays that
cost outside the timed render.

## Escaping benchmark

```sh
uv run benchmarks/escaping.py
```

Renders an article with a heading and 50 paragraphs, sweeping exact paragraph
lengths of 16, 63, 64, 65, 256, and 600 characters. The 63/64/65 cases bracket
the escaping implementation's 64-character threshold. Text is repeated and
truncated without adding index prefixes or trimming whitespace, so the printed
character count is the actual length passed to the escaper, not its UTF-8 size.
Short cases include element-construction overhead; these are complete article
benchmarks, not isolated escaper timings.

Six text variants cover clean ASCII, clean Unicode, prose with an occasional
`&`, ASCII and non-ASCII text dense with `&`, `<`, and `>`, and text containing
all five escaped characters (`&`, `<`, `>`, double quote, and apostrophe).
The **htmpy** path builds a `p` element per paragraph, **htmpy repeat** uses
`p.repeat(paragraphs)`, and **Jinja** renders a
compiled, autoescaped template with a `for` loop. Each variant is checked
against independently escaped expected HTML before timing.

htmpy and Jinja use the same escaping conventions, so their output is identical,
including `&#34;` and `&#39;` for quotes. htmpy calls markupsafe's C escaper
directly for strings shorter than 64 characters, where its single pass is
cheapest, and otherwise checks each special character with `in`, which uses a
vectorized scan, and runs one `str.replace` pass only for the characters that are
present. Long clean text and ordinary prose therefore cost a few scans rather
than a per-character loop, while long text dense with special characters pays
for several passes and trails the single C pass Jinja uses. Jinja adds its own
per-item template overhead on top of escaping. Results report UTF-8 output
size and median time per article across five repeats of 1,000 articles, with
input preparation, Jinja compilation, validation, and printing excluded.
