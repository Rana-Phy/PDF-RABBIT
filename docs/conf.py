# Configuration file for the Sphinx documentation builder.
# Docs are written in Markdown (via MyST). You never edit HTML.

project = "PDF-RABBIT"
copyright = "2026, Rana Hossain"
author = "Rana Hossain"
release = "0.1.0"

# Extensions. NOTE: sphinx.ext.viewcode is deliberately NOT included,
# so no "view source" links are ever added (keeps the code closed).
extensions = [
    "myst_parser",          # lets you write pages in Markdown
]

# Accept both Markdown and reStructuredText source files.
source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The Glassure look: Read the Docs theme.
html_theme = "sphinx_rtd_theme"
html_title = "PDF-RABBIT"

# Handy Markdown features (admonitions, definition lists, etc.)
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

html_logo = "logo.jpg"
html_favicon = "logo.jpg"

html_static_path = ["_static"]
html_css_files = ["custom.css"]
