# Contributing

We welcome contributions to the BEAM ecosystem! Whether it's reporting issues,
suggesting features, improving the documentation, or submitting pull requests,
your input helps improve these tools for the community.

## How to Contribute

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

### Style

We follow [PEP 8](https://peps.python.org/pep-0008/) and use the
following tools:

- [ruff](https://github.com/astral-sh/ruff) for linting
- [black](https://black.readthedocs.io/en/stable/) for formatting
- [isort](https://pycqa.github.io/isort/) for sorting imports

To run these tools locally, install the optional dependencies and run:

```bash
pip install "sdf-xarray[lint]"
ruff check
```

### Running and Adding Tests

We use [pytest](https://docs.pytest.org/en/stable/) to run tests.
All new functionality should include relevant tests, placed in the `tests/`
directory and following the existing structure.

Before submitting code changes, ensure that all tests pass:

```bash
pip install "sdf-xarray[test]"
pytest
```

## Documentation

### Style

When contributing to the documentation:

- Wrap lines at 80 characters.
- Follow the format of existing `.rst` files.
- Link to external functions or tools when possible.

### Compiling and Adding Documentation

To build the documentation locally, first install the required packages:

```bash
pip install "sdf-xarray[docs]"
cd docs
make html
```
Every time you make changes to the documentation or add a new page, you must
re-run the `make html` command to regenerate the HTML files.

### Previewing Documentation

#### Using VS Code Extensions

Once the html web pages have been made you can review them installing the
[Live Server](https://marketplace.visualstudio.com/items/?itemName=ritwickdey.LiveServer)
VS Code extension. Navigate to the `_build/html` folder, right-click the
`index.html`, and select **"Open with Live Server"**. This
will open a live preview of the documentation in your web browser.

#### Using a Simple Python Server

Alternatively, if you're not using VS Code, you can start a simple local server with Python:

```bash
python -m http.server -d _build/htm
```

Then open http://localhost:8000 in your browser to view the documentation.

## Continuous Integration

All pull requests are automatically checked using GitHub Actions for:

- Linting (`ruff`)
- Formatting (`black` and `isort`)
- Testing (`pytest`)

These checks must pass before a pull request can be merged.
