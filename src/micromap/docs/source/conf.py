# Configuration file for the Sphinx documentation builder.

# -- Path setup
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

# -- Project information

project = 'MicroMAP'
copyright = '2022, João Pedro C. Moreira'
author = 'João Pedro C. Moreira '

release = '0.1'
version = '0.1'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.autodoc',
]

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'
html_logo = 'img/logo.png'
