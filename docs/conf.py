# Configuration file for the Sphinx documentation builder.
# Docs are written in Markdown (via MyST). You never edit HTML.
project = "PDF-RABBIT"
copyright = "2026, Rana Hossain"
author = "Rana Hossain"
release = "0.1.0"

extensions = [
    "myst_parser",          # lets you write pages in Markdown
]

source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Stock Read the Docs theme — no customizations.
html_theme = "sphinx_rtd_theme"
html_title = "PDF-RABBIT"
html_logo = "logo.png"
html_favicon = "logo.png"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
