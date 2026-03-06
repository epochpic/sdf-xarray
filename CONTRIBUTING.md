# Contributing

We welcome contributions to the BEAM ecosystem! Whether it's reporting issues,
suggesting features, improving the documentation, or submitting pull requests,
your input helps improve these tools for the community.

## How to contribute

There are many ways to get involved:

- **Report bugs** - Found something not working as expected? Open an issue
  with as much detail as possible.
- **Request a feature** - Got an idea for a new feature or enhancement?
  Open a feature request on
  [GitHub Issues](https://github.com/epochpic/sdf-xarray/issues).
- **Improve the documentation** - If something is missing or unclear, feel free
  to suggest edits or open a pull request.
- **Submit code changes** - Bug fixes, refactoring, and new features are
  all welcome.

## Code

```bash
git clone --recursive https://github.com/epochpic/sdf-xarray.git
cd sdf-xarray
pip install .
```

### Style

We use [Ruff](https://docs.astral.sh/ruff/) to maintain code quality and
formatting. This can be installed locally via the `lint` dependency group:

```bash
pip install --group lint
```

Ruff can then be run with:

```bash
ruff check src tests
```

Alternatively, `uv` users can do this in one step with `uv run`:

```bash
uv run ruff check src tests
```

Many of the issues raised by Ruff can be fixed automatically:

```bash
ruff check --fix src tests
```

Ruff may also be used to format the code to a style similar to that enforced by
[Black](https://black.readthedocs.io/en/stable/), which (almost) matches the
[PEP-8 standard](https://peps.python.org/pep-0008/):

```bash
ruff format src tests
```

### Running and adding tests

We use [pytest](https://docs.pytest.org/en/stable/) to run tests.
All new functionality should include relevant tests, placed in the `tests/`
directory and following the existing structure.

When running the tests for the first time you will need an internet connection
in order to download the datasets.

Before submitting code changes, ensure that all tests pass:

```bash
pip install --group test
pytest
```

Alternatively, `uv` users can use:

```bash
uv run pytest
```

## Documentation

```{note}
When compiling the documentation for the first time you will need an internet
connection in order to download the datasets.
```

The documentation is stored under the `/docs` folder and is written in Markdown
files following the [MyST-NB](https://myst-nb.readthedocs.io/en/latest/index.html)
format.

To build the documentation locally, first install the required packages:

```bash
pip install --group docs
cd docs
make html
```

The documentation can be updated by changing any of the `*.md` files located
in the main `docs` directory. The existing documentation hopefully includes most
of the snippets you'd need to write or update it, however if you are stuck
please don't hesitate to reach out.

### Building the documentation

#### Auto-building

Run the following command from the `docs` folder in order to auto-rebuild the
documentation when you save changes in any of the `docs/*.md`, `src/sdf_xarray/*.py`
or update the `CONTRIBUTING.md` file:

```bash
make livehtml
```

This should spin up a local server for the documentation which you can open in your
browser. Example output including what changing a file should produce in the terminal:

```bash
[sphinx-autobuild] Starting initial build
[sphinx-autobuild] > python -m sphinx build . _build/html --builder html --quiet
[sphinx-autobuild] Serving on http://127.0.0.1:8000
[sphinx-autobuild] Waiting to detect changes...
[sphinx-autobuild] Detected changes (key_functionality.md)
[sphinx-autobuild] Rebuilding...
[sphinx-autobuild] > python -m sphinx build . _build/html --builder html --quiet
[sphinx-autobuild] Serving on http://127.0.0.1:8000
```

#### Manual building

Alternatively if you wish to rebuild the documentation manually run the following
command from the `docs` folder:

```bash
make html
```

Once the html web pages have been made you can review them by installing the
[Live Server](https://marketplace.visualstudio.com/items/?itemName=ritwickdey.LiveServer)
VS Code extension. Navigate to the `docs/_build/html` folder, right-click the
`index.html`, and select **"Open with Live Server"**. This
will open a live preview of the documentation in your web browser.

## Continuous integration

All pull requests are automatically checked using GitHub Actions for:

- Linting and formatting (`ruff`)
- Testing (`pytest`)
- Cross-platform building (`cibuildwheel`)

These checks must pass before a pull request can be merged.
