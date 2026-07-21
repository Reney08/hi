import os
import sys
# Pfad zum Hauptordner (barbot_project), damit Sphinx app.py findet
sys.path.insert(0, os.path.abspath('../../'))

project = 'BarBot'
copyright = '2026, rmlodoch'
author = 'rmlodoch'
release = '1.1.0'

# Wichtige Erweiterungen aktivieren:
# - autodoc: Liest Docstrings aus
# - napoleon: Unterstützt Google- und NumPy-Style Docstrings
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinxcontrib.httpdomain',
    'sphinxcontrib.autohttp.flask',# Fügt Links zum Quellcode hinzu
]

templates_path = ['_templates']
exclude_patterns = []

language = 'de'

# Ein schickes, modernes Theme auswählen
html_theme = 'furo' 
html_static_path = ['_static']