# Agent Guidance

## Project overview

htmlkit builds HTML with Python objects. It requires Python 3.14 or newer and uses
uv for the Python development environment.

## Code style

- Adhere to the PEP 8 style guide when writing Python code.
- Use Python type annotations for functions and classes. Prefix variables,
  functions, methods, and classes with `_` for private implementations.
- Use Google-style docstrings to explain functionality of the code.
- Keep module and public API docstrings concise and focused on behavior.
- Use ruff to check code style and format. Configuration settings for ruff is in
  the pyproject.toml file.
- Prefer small changes within the existing modules over new layers or helpers.
- Use short but informative names for tests.

## Development environment

- Run commands from the repository root. The project uses uv-managed Python.
- Use `uv sync` to manage the Python environment and dependencies.
- Use `uv run` for project commands rather than relying on a globally installed
  Python or manually changing `PYTHONPATH`.
- When changing dependencies, use the `uv add` or `uv remove` commands to update
  `pyproject.toml` and `uv.lock` together.
- Do not commit virtual environments, caches, build output, or local secrets.

## Testing instructions

Run the standard checks after changing Python code:

```sh
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

For a focused test run during development:

```sh
uv run pytest tests/test_elements.py -k escaping
```

## Performance checks

Run the benchmark scripts to evaluate performance of the package after critical
changes have been made to the source code. Benchmarks do not need to be run for
minor or less critical changes.

```sh
uv run benchmarks/simple_page.py
uv run benchmarks/unordered_list.py
```
