import datetime as dt
import subprocess

# -- System information ------------------------------------------------------

subprocess.run(["pip", "list"])


# -- Project information -----------------------------------------------------

project = "xarray-ceos-alos2"
author = f"{project} developers"
initial_year = "2023"
year = dt.datetime.now().year
copyright = f"{initial_year}-{year}, {author}"

# The root toctree document.
root_doc = "index"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "IPython.sphinxext.ipython_directive",
    "IPython.sphinxext.ipython_console_highlighting",
]

extlinks = {
    "issue": ("https://github.com/umr-lops/xarray-ceos-alos2/issues/%s", "GH%s"),
    "pull": ("https://github.com/umr-lops/xarray-ceos-alos2/pull/%s", "PR%s"),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "directory"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]

# -- Options for the intersphinx extension -----------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/stable/", None),
    "xarray": ("https://docs.xarray.dev/en/latest/", None),
    "datatree": ("https://xarray-datatree.readthedocs.io/en/latest/", None),
}


# -- Options for the autosummary extension -----------------------------------

autosummary_generate = True
autodoc_typehints = "none"
napoleon_use_param = False
napoleon_use_rtype = True

napoleon_preprocess_types = True
napoleon_type_aliases = {}


# -- Options for the myst-parser extension -----------------------------------

myst_enable_extensions = ["colon_fence"]
