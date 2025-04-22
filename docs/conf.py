# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from contextlib import suppress
from importlib.metadata import version as get_version
from pathlib import Path

with suppress(ImportError):
    import matplotlib

    matplotlib.use("Agg")
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "sdf-xarray"
copyright = "2024-2025, Peter Hill, Joel Adams"
author = "Peter Hill, Joel Adams"

# The full version, including alpha/beta/rc tags
release = get_version("sdf_xarray")
# Major.minor version
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.coverage",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_autodoc_typehints",
    "IPython.sphinxext.ipython_directive",
    "IPython.sphinxext.ipython_console_highlighting",
    "myst_parser",
]

# Sometimes the savefig directory doesn't exist and needs to be created
# https://github.com/ipython/ipython/issues/8733
# becomes obsolete when we can pin ipython>=5.2; see ci/requirements/doc.yml
ipython_savefig_dir = Path(__file__).resolve().parent / "_build" / "html" / "_static"
ipython_savefig_dir.mkdir(parents=True, exist_ok=True)
ipython_savefig_dir = str(ipython_savefig_dir)

autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Numpy-doc config
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_attr_annotations = True
napoleon_preprocess_types = True

# Enable numbered references
numfig = True

autodoc_type_aliases = {
    "ArrayLike": "numpy.typing.ArrayLike",
}

autodoc_default_options = {"ignore-module-all": True}
autodoc_typehints = "description"
autodoc_class_signature = "mixed"

# The default role for text marked up `like this`
default_role = "any"

# Tell sphinx what the primary language being documented is.
primary_domain = "py"

# Tell sphinx what the pygments highlight language should be.
highlight_language = "python"

# Include "todo" directives in output
todo_include_todos = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]
html_static_path = []

html_theme_options = {
    "repository_url": "https://github.com/epochpic/sdf-xarray",
    "repository_branch": "main",
    "path_to_docs": "docs",
    "use_edit_page_button": True,
    "use_repository_button": True,
    "use_issues_button": True,
    "home_page_in_toc": False,
}

pygments_style = "sphinx"

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "xarray": ("https://docs.xarray.dev/en/latest", None),
    "pint": ("https://pint.readthedocs.io/en/stable", None),
    "pint-xarray": ("https://pint-xarray.readthedocs.io/en/stable", None),
}
