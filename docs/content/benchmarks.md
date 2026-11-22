# Benchmarks

These benchmarks compare htmlkit with compiled, autoescaped Jinja templates. Each script checks the rendered HTML before timing it. Times are medians per complete render, in microseconds (µs); lower is better.

The results below were measured on an Apple M4 (arm64), macOS 27.2.1, with Python 3.14.3, htmlkit 26.11, Jinja 3.1.6, and MarkupSafe 3.0.4. To repeat a benchmark, run its command from the project root. Jinja is a development dependency, not an htmlkit runtime dependency.

## Simple page benchmark

```bash
uv run benchmarks/simple_page.py
```

| Renderer | µs/page |
| :--- | ---: |
| htmlkit fresh | 2.84 |
| htmlkit reused | 1.18 |
| Jinja | 3.01 |

The benchmark creates the same HTML document with htmlkit and Jinja: a head containing a UTF-8 charset meta element and a stylesheet link, followed by a heading and paragraph, with a language attribute and paragraph class. Both implementations escape dynamic text and return a complete HTML string. The script checks all three outputs against the expected HTML before timing.

The benchmark reports three paths:

- **htmlkit fresh** constructs every element with keyword attributes on each iteration.
- **htmlkit reused** prepares the static head and the HTML and paragraph attribute templates once. Each iteration constructs fresh dynamic elements, escapes the heading and message, and renders a complete page. It uses the existing immutable element API; it does not cache completed pages or dynamic text.
- **Jinja** reuses a template compiled once outside the timed section.

The reused htmlkit path and Jinja both exclude static preparation, as applications can do when reusing templates. The fresh htmlkit path is retained to show the cost of rebuilding everything. Imports, preparation, validation, and printing are excluded from the timings; there is no file or network I/O.

Results report the median time per page across five repeats of 10,000 pages using Python's `timeit` (which disables garbage collection during timing). Lower is faster. Timings depend on the machine and Python version; this small page is not representative of every workload.

## Unordered list benchmark

```bash
uv run benchmarks/unordered_list.py
```

| Renderer | µs/list (1,000 items) |
| :--- | ---: |
| htmlkit | 225.44 |
| htmlkit repeat | 61.05 |
| Jinja | 241.29 |

Creates an unordered list with 1,000 list items. The original htmlkit path uses a Python list comprehension to construct fresh `li` elements and passes them to `ul`. The **htmlkit repeat** path uses `ul(li.repeat(items))`, avoiding intermediate element objects. The Jinja path uses a template for-loop over the same input strings. All three return complete HTML strings and escape dynamic text containing `&` and angle brackets. The script checks all three outputs against independently constructed expected HTML before timing.

Like the simple page benchmark, this reports median time using five `timeit` repeats, with input preparation, Jinja compilation, validation, and printing excluded. Each repeat renders 1,000 lists rather than 10,000 pages to keep the larger workload practical. Results are in microseconds per complete list, not per item. There is no separate htmlkit reused path because the bare `ul` and `li` elements already serve as reusable templates; no static subtrees or attribute values need preparation.

## Fragment benchmark

```bash
uv run benchmarks/fragments.py
```

Compares `Fragment(*children)`, `Fragment.from_iterable(children)`, and compiled, autoescaped Jinja templates for two workloads without a wrapping element:

- A small fragment with a heading, separator text, and paragraph.
- A fragment containing 1,000 generated paragraphs.

| Renderer | Small fragment (µs) | 1,000 paragraphs (µs) |
| :--- | ---: | ---: |
| `Fragment` | 0.82 | 241.15 |
| `Fragment.from_iterable` | 0.79 | 244.06 |
| `p.repeat` | — | 68.60 |
| Jinja | 3.02 | 248.83 |

The small iterable case uses a tuple. The two large constructor cases generate fresh `p` elements: `Fragment` expands a generator into positional arguments, while `from_iterable` consumes a generator directly. Element construction, escaping, and rendering the final string are included in the timings. No rendered children are cached. Input strings and Jinja templates are prepared outside the timings. This measures complete rendering paths, not isolated fragment-wrapper overhead.

The large workload also includes `p.repeat(ITEMS)`, which returns a fragment without allocating an element for each paragraph. It reuses the paragraph's opening and closing tags while still escaping every input string. The mixed-tag small workload has no equivalent single-tag `repeat()` case.

Before timing, all outputs for each workload must equal independently constructed expected HTML, including escaped ampersands and angle brackets. The script reports median microseconds per complete fragment across five repeats of 10,000 small fragments or 1,000 large fragments. As with the other benchmarks, `timeit` disables garbage collection, and results depend on the machine and Python version. These are eager renders, not streaming or peak-memory measurements.

## Deep nesting benchmark

```bash
uv run benchmarks/nested.py
```

Builds a fresh paragraph inside 10, 32, and 100 nested wrappers, using both a short text payload and a payload 256 times larger. Four shapes are measured:

- Identical bare `div` wrappers, preserving the original baseline.
- Alternating bare `div` and `section` wrappers.
- Alternating wrappers with a fresh `data-level` attribute at every level.
- Alternating wrappers with a trailing `span` containing the level number.

Levels count outward from zero around the paragraph. Attributes and siblings are separate cases so their costs can be distinguished. Each render includes escaping the paragraph text, constructing every wrapper, and returning the complete HTML string. No intermediate elements are retained after their parent is constructed. Real documents rarely nest deeper than 32 elements, the depth Lighthouse flags as excessive, so 100 is a stress case rather than a target.

The Jinja path uses a compiled, autoescaped template with loops that emit the opening wrappers, the escaped paragraph, and the closing wrappers. The mixed template also selects alternating tags and emits attributes or siblings as needed. It produces the same nested HTML without recursive macros or repeated subtree construction. This compares complete output generation, not equivalent component-call trees. Template compilation is excluded from both time and memory measurements, as in the other benchmarks; no completed output is cached.

Every case is checked against independently assembled expected HTML, including escaped ampersands and angle brackets, before timing. Input preparation and validation are excluded. The output reports UTF-8 output size and median time across five repeats of 100 renders, with `timeit` disabling garbage collection. Each depth and payload combination reports both htmlkit and Jinja results.

Peak memory is measured separately with `tracemalloc`, using the median of five single renders and a fresh tracing session for each sample. The final string remains alive when the peak is read. Tracing is disabled during timing, and inputs and expected strings are allocated before tracing starts. The reported peak covers traced Python allocations, not process RSS or total bytes allocated over the render's lifetime.

When an element wraps a single element with the same tag, or wraps such a run, htmlkit stores a reference to the child and a run count instead of copying the child's rendered HTML, then renders the chain once when the HTML is first read. The identical-tag chain of depth d around an escaped payload of length n costs O(d + n) copying and live storage, rather than O(d² + d·n) copying. Wrapping a single element with a different tag, such as `li(a(...))`, copies eagerly, because that is cheaper than materializing a one-level chain later. The mixed cases do not start an identical-tag run, so they expose repeated copying of the growing subtree. Peak live memory does not measure cumulative copying. For the identical-tag baseline, the remaining per-level cost is one Python call and one object allocation. On this machine, htmlkit was faster at depth 10, the renderers were within 0.3 µs at depth 32, and Jinja was faster at depth 100 for both payload sizes in that baseline. Retaining all intermediate elements would be a different memory workload.

### Identical tags

| Text chars | Depth | Output bytes | htmlkit (µs) | Jinja (µs) | htmlkit peak (KiB) | Jinja peak (KiB) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 10 | 147 | 2.22 | 3.89 | 0.51 | 2.84 |
| 20 | 32 | 389 | 5.26 | 5.30 | 0.98 | 3.48 |
| 20 | 100 | 1,137 | 15.03 | 9.14 | 2.44 | 5.43 |
| 5,120 | 10 | 7,797 | 11.81 | 13.48 | 15.45 | 17.78 |
| 5,120 | 32 | 8,039 | 14.84 | 14.59 | 15.92 | 18.42 |
| 5,120 | 100 | 8,787 | 24.59 | 18.64 | 17.38 | 20.37 |

### Mixed tags

| Text chars | Depth | Output bytes | htmlkit (µs) | Jinja (µs) | htmlkit peak (KiB) | Jinja peak (KiB) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 10 | 187 | 2.71 | 5.38 | 0.71 | 3.03 |
| 20 | 32 | 517 | 7.95 | 9.00 | 1.35 | 3.89 |
| 20 | 100 | 1,537 | 25.44 | 20.25 | 3.34 | 6.45 |
| 5,120 | 10 | 7,837 | 12.62 | 14.82 | 15.65 | 17.98 |
| 5,120 | 32 | 8,167 | 19.62 | 18.79 | 16.29 | 18.83 |
| 5,120 | 100 | 9,187 | 41.08 | 29.89 | 18.29 | 21.39 |

### Mixed tags with attributes

| Text chars | Depth | Output bytes | htmlkit (µs) | Jinja (µs) | htmlkit peak (KiB) | Jinja peak (KiB) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 10 | 337 | 6.07 | 7.79 | 1.14 | 4.17 |
| 20 | 32 | 1,019 | 19.20 | 17.20 | 2.47 | 7.68 |
| 20 | 100 | 3,127 | 60.34 | 44.18 | 6.59 | 18.94 |
| 5,120 | 10 | 7,987 | 16.45 | 17.37 | 16.08 | 19.11 |
| 5,120 | 32 | 8,669 | 31.26 | 26.82 | 17.41 | 22.62 |
| 5,120 | 100 | 10,777 | 77.39 | 54.61 | 21.53 | 33.88 |

### Mixed tags with siblings

| Text chars | Depth | Output bytes | htmlkit (µs) | Jinja (µs) | htmlkit peak (KiB) | Jinja peak (KiB) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 10 | 327 | 5.96 | 7.91 | 1.20 | 4.16 |
| 20 | 32 | 987 | 18.86 | 17.17 | 2.48 | 7.65 |
| 20 | 100 | 3,027 | 58.99 | 44.73 | 6.47 | 18.84 |
| 5,120 | 10 | 7,977 | 16.71 | 17.64 | 16.14 | 19.10 |
| 5,120 | 32 | 8,637 | 31.65 | 27.29 | 17.43 | 22.59 |
| 5,120 | 100 | 10,677 | 77.36 | 54.69 | 21.41 | 33.78 |

## Realistic page benchmark

```bash
uv run benchmarks/realistic_page.py
```

| Renderer | µs/page (12,083 bytes) |
| :--- | ---: |
| htmlkit fresh | 185.91 |
| htmlkit reused | 152.63 |
| htmlkit repeat | 62.39 |
| Jinja | 106.60 |

Builds a complete inventory page of about 12 KB: a head with charset, title, and stylesheet; a header with a five-link navigation list whose current link carries an `active` class and a heading; a main section with a 50-row, 6-column data table whose cells mix integers, escaped names, non-ASCII owners, a status class attribute, and an edit link with `&` in its URL; a form with ten label and input pairs using the boolean `required` attribute, a select with a conditionally `selected` option, a textarea, and a submit button; and a footer with a `time` element. The page has about 430 elements and 370 escaped values, so element construction dominates rather than any single long string.

The **htmlkit fresh** path builds every element with keyword attributes on each render. The **htmlkit reused** path prepares the static head, header, table head, footer, and attributed `html`, `table`, `td`, `form`, and `select` templates once, then builds the table body and form fields on each render. The **htmlkit repeat** path is the reused page with the table rows rendered from a `tr` template whose cells hold `each` placeholders, filled by one `repeat()` call. The **Jinja** path renders one compiled, autoescaped template with `for` loops and `if` conditions for the same context. Conditional attributes use `None` values in htmlkit, which omit the attribute, and `{% if %}` blocks in Jinja. All four outputs must equal independently assembled expected HTML before timing.

Results report the median time per page across five repeats of 1,000 pages, with input preparation, Jinja compilation, validation, and printing excluded. Every htmlkit element costs one Python call and one allocation, so pages with hundreds of small elements, such as table cells, are where a compiled template that emits static text in bulk has its largest advantage. Keyword attributes add to that: each attributed element normalizes its names through a cached lookup, renders the values, and allocates a new tag definition, which costs roughly three times as much as an element with only text. Preparing attributed elements once, as the reused path does with `td(class_="number")`, pays that cost outside the timed render. A bound template removes the per-element cost from the rows entirely: `repeat()` compiles the template's HTML into static pieces and slots for bound values the first time it is filled. Each batch copies the pieces once, then reuses the slots across rows. Each row calls its accessors, escapes the values, fills the slots, and joins the pieces, avoiding per-row format string parsing and argument expansion. The batch-local copy keeps recursive bindings from overwriting an outer row's content.

## Escaping benchmark

```bash
uv run benchmarks/escaping.py
```

Renders an article with a heading and 50 paragraphs, sweeping exact paragraph lengths of 16, 63, 64, 65, 256, and 600 characters. The 63/64/65 cases are kept from an earlier escaper that switched strategy at 64 characters, so the sweep still covers short, medium, and long text. Text is repeated and truncated without adding index prefixes or trimming whitespace, so the printed character count is the actual length passed to the escaper, not its UTF-8 size. Short cases include element-construction overhead; these are complete article benchmarks, not isolated escaper timings.

Six text variants cover clean ASCII, clean Unicode, prose with an occasional `&`, ASCII and non-ASCII text dense with `&`, `<`, and `>`, and text containing all five escaped characters (`&`, `<`, `>`, double quote, and apostrophe). The **htmlkit** path builds a `p` element per paragraph, **htmlkit repeat** uses `p.repeat(paragraphs)`, and **Jinja** renders a compiled, autoescaped template with a `for` loop. Each variant is checked against independently escaped expected HTML before timing.

htmlkit and Jinja use the same escaping conventions, so their output is identical, including `&#34;` and `&#39;` for quotes. htmlkit calls markupsafe's C escaper directly for every string, so escaping itself costs the same single pass in both libraries and the difference comes from per-paragraph overhead: a `p` element call and allocation in htmlkit versus a loop iteration and template output in Jinja. For 600-character paragraphs containing all five specials, htmlkit and Jinja took nearly the same time, while `p.repeat` was faster. Results report UTF-8 output size in decimal KB and median time per article across five repeats of 1,000 articles, with input preparation, Jinja compilation, validation, and printing excluded.

### ASCII, no specials

| Chars/paragraph | Output (KB) | htmlkit (µs) | htmlkit repeat (µs) | Jinja (µs) |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 1.2 | 10.52 | 2.86 | 13.42 |
| 63 | 3.6 | 12.78 | 5.06 | 15.83 |
| 64 | 3.6 | 12.75 | 4.95 | 15.68 |
| 65 | 3.7 | 12.75 | 4.93 | 15.75 |
| 256 | 13.2 | 22.83 | 14.51 | 25.75 |
| 600 | 30.4 | 40.94 | 30.95 | 43.43 |

### Unicode, no specials

| Chars/paragraph | Output (KB) | htmlkit (µs) | htmlkit repeat (µs) | Jinja (µs) |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 1.5 | 10.73 | 2.92 | 13.49 |
| 63 | 4.8 | 12.86 | 4.95 | 15.69 |
| 64 | 4.8 | 13.00 | 5.04 | 15.79 |
| 65 | 4.9 | 12.96 | 5.05 | 15.88 |
| 256 | 18.1 | 25.00 | 14.45 | 26.55 |
| 600 | 41.8 | 43.40 | 33.86 | 44.62 |

### Prose, occasional `&`

| Chars/paragraph | Output (KB) | htmlkit (µs) | htmlkit repeat (µs) | Jinja (µs) |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 1.4 | 11.80 | 4.09 | 14.88 |
| 63 | 3.8 | 15.75 | 7.84 | 18.69 |
| 64 | 3.8 | 15.99 | 7.91 | 18.94 |
| 65 | 3.9 | 15.96 | 8.05 | 19.01 |
| 256 | 14.0 | 33.26 | 24.55 | 35.43 |
| 600 | 32.4 | 65.92 | 55.61 | 68.77 |

### ASCII with `& < >`

| Chars/paragraph | Output (KB) | htmlkit (µs) | htmlkit repeat (µs) | Jinja (µs) |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 1.6 | 12.05 | 4.19 | 15.80 |
| 63 | 5.1 | 16.83 | 8.70 | 19.74 |
| 64 | 5.1 | 17.24 | 8.72 | 19.60 |
| 65 | 5.2 | 16.91 | 8.71 | 19.69 |
| 256 | 19.4 | 36.87 | 27.64 | 38.96 |
| 600 | 44.9 | 71.29 | 60.10 | 77.07 |

### Non-ASCII with `& < >`

| Chars/paragraph | Output (KB) | htmlkit (µs) | htmlkit repeat (µs) | Jinja (µs) |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 1.7 | 12.11 | 4.21 | 14.87 |
| 63 | 6.0 | 17.40 | 9.07 | 19.78 |
| 64 | 6.0 | 17.81 | 9.18 | 20.08 |
| 65 | 6.1 | 17.79 | 8.95 | 20.16 |
| 256 | 23.1 | 39.92 | 29.17 | 42.36 |
| 600 | 53.5 | 77.78 | 64.55 | 78.20 |

### All five specials

| Chars/paragraph | Output (KB) | htmlkit (µs) | htmlkit repeat (µs) | Jinja (µs) |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 2.6 | 12.49 | 4.44 | 15.11 |
| 63 | 8.7 | 17.89 | 9.37 | 20.63 |
| 64 | 8.7 | 18.27 | 9.85 | 20.84 |
| 65 | 8.8 | 18.46 | 9.57 | 20.90 |
| 256 | 32.8 | 40.75 | 30.54 | 44.10 |
| 600 | 75.6 | 82.64 | 69.68 | 82.59 |
