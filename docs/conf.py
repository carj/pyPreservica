import sphinx_rtd_theme
import os
import sys


sys.path.insert(0, os.path.abspath('..'))


master_doc = 'index'

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
    'sphinx.ext.todo',
]

html_theme = "sphinx_rtd_theme"

pygments_style = 'default'

source_suffix = ".rst"

project = u"pyPreservica"
author = u"James Carr"
