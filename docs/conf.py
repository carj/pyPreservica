import sphinx_rtd_theme

master_doc = 'index'

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
]

html_theme = "sphinx_rtd_theme"

pygments_style = 'paraiso-dark'