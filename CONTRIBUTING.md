# Contributing to htmlkit

Search the [open issues](https://github.com/wigging/htmlkit/issues) before opening a bug report or feature request. For a rendering bug, include a small Python example, the HTML you expected, and the HTML you got. Report suspected vulnerabilities privately as described in the [security policy](SECURITY.md).

## Making a change

Fork the repository, clone your fork, and create a branch for your change. From the repository root, install the development dependencies with [uv](https://docs.astral.sh/uv/) and Python 3.14 or newer:

```bash
uv sync
```

For a bug fix, add a test in `tests/` that fails without the fix. If the change affects how people use htmlkit, update the relevant guide in `docs/content/`. Run the same checks as CI before opening a pull request:

```bash
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

In the pull request, describe what changed and why, and link the issue if there is one. The [code of conduct](CODE_OF_CONDUCT.md) applies to issues, pull requests, and reviews.
