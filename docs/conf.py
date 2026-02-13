import sphinx_rtd_theme
import os
import sys
from pyPreservica import __version__

sys.path.insert(0, os.path.abspath('../pyPreservica/'))

master_doc = 'index'

html_logo = "images/trace.svg"

extensions = [
    'sphinx.ext.apidoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
    'sphinx.ext.todo',
    'sphinx.ext.autosectionlabel',
    'sphinxcontrib.googleanalytics'
]

#html_theme = "sphinx_rtd_theme"

html_theme = "sphinx_clarity_theme"

html_extra_path = ["googled4940437d6a0a50d.html"]

html_theme_options = {
    'analytics_id': 'G-FWD081Y5Z6'}


default_dark_mode = False

version = __version__

pygments_style = 'default'

source_suffix = ".rst"

project = u"pyPreservica"
author = u"James Carr"

googleanalytics_id = 'G-FWD081Y5Z6'