import os
import sys

sys.path.insert(0, os.path.abspath("../src"))
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "ledge"
copyright = "2025, Chase Horton"
author = "Chase Horton"
release = "0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autodoc_typehints = "description"
add_module_names = False

napoleon_google_docstring = True
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
autodoc_type_aliases = {
    "Decimal": "decimal.Decimal",
    "Optional": "typing.Optional",
    "datetime": "~datetime.datetime",
    "List": "typing.List",
}
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


def setup(app):
    """Add custom CSS file to the HTML output."""
    app.add_css_file("custom.css")
