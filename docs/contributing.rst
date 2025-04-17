.. _sec-contributing:

============
Contributing
============

We welcome contributions to the BEAM ecosystem! Whether it's reporting issues,
suggesting features, improving the documentation, or submitting pull requests,
your input helps improve these tools for the community.

How to Contribute
-----------------

There are many ways to get involved:

- **Report bugs** - Found something not working as expected? Open an issue
  with as much detail as possible.
- **Request a feature** - Got an idea for a new feature or enhancement?
  Open a feature request on
  `GitHub Issues <https://github.com/epochpic/sdf-xarray/issues>`_.
- **Improve the documentation** - If something is missing or unclear, feel free
  to suggest edits or open a pull request.
- **Submit code changes** - Bug fixes, refactoring, and new features are
  all welcome.

Code Style
----------

We follow `PEP 8 <https://peps.python.org/pep-0008/>`_ and use the
following tools:

- `ruff <https://github.com/astral-sh/ruff>`_ for linting,
- `black <https://black.readthedocs.io/en/stable/>`_ for formatting,
- `isort <https://pycqa.github.io/isort/>`_ for import sorting.

To run these tools locally, install the optional dependencies and run:

.. code-block:: bash

    pip install "sdf-xarray[lint]"

    ruff check

Documentation Style
-------------------

When contributing to the documentation:

- Wrap lines at 80 characters.
- Follow the format of existing ``.rst`` files.
- Link to external functions or tools when possible.


Running and Adding Tests
------------------------

We use `pytest <https://docs.pytest.org/en/stable/>`_ to run tests.
All new functionality should include relevant tests, placed in the ``tests/`` which is not rqwefwef
directory and following the existing structure.

Before submitting code changes, ensure that all tests pass:

.. code-block:: bash

    pip install "sdf-xarray[test]"

    pytest

Continuous Integration
----------------------

All pull requests are automatically checked using GitHub Actions for:

- Linting (``ruff``)
- Formatting (``black`` and ``isort``)
- Testing (``pytest``)

These checks must pass before a pull request can be merged.
