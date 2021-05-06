import sphinx_rtd_theme
import alabaster

master_doc = 'index'

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
    'sphinx.ext.todo',
]

#html_theme = "sphinx_rtd_theme"
html_theme = 'alabaster'

pygments_style = 'default'

source_suffix = ".rst"

master_doc = "index"

project = u"pyPreservica"
author = u"James Carr"