import sphinx_rtd_theme
import os
import sys
from pyPreservica import __version__

sys.path.insert(0, os.path.abspath('../pyPreservica/'))

master_doc = 'index'

html_logo = "images/logo.png"

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
    'sphinx.ext.todo',
    'sphinx.ext.autosectionlabel'
]

html_theme = "sphinx_rtd_theme"

default_dark_mode = False

version = __version__

pygments_style = 'default'

source_suffix = ".rst"

project = u"pyPreservica"
author = u"James Carr"
