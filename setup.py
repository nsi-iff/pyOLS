#!/usr/bin/env python
# Make sure we've got setuptools installed before
# anything else happens
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
import sys
from os import path

install_requires = [
    'SQLAlchemy == 0.4.6', # The 0.5 beta breaks Elixir :(
    'Elixir >= 0.5.2',
    'scgi'
    ]

if sys.version_info < (2, 5):
    # Python 2.5 and up comes with sqlite
    install_requires.append('pysqlite >= 2.2')

if 'develop' in sys.argv:
    # Only install testing tools if we're going to run in develop mode
    install_requires.extend([
        # Needed for running the test suite
        'nose >= 0.10.1',
        # Needed for checking dot files (tests/test_graphviz.py)
        'pyparsing >= 1.5.0',
    ])

setup_requires = []
if path.exists(path.join(path.dirname(__file__), '.bzr')):
    # If we're inside a bzr repository,
    # make sure setuptools_bzr is installed
    setup_requires = ['setuptools_bzr']

setup(
    name = 'pyOLS',
    version = '0.1a',
    description = 'Python Remote Ontology provides functions for creating, '
                  'searching and graphing ontologies over XML-RPC.',
    author = 'David Wolever',
    author_email = 'david@wolever.net',
    url = 'http://nsi.cefetcampos.br/softwares/pyols/',
    setup_requires=setup_requires,
    install_requires = install_requires,
    packages=find_packages(),
    include_package_data=True,
    entry_points= {
        'console_scripts':
            ['pyols = pyols.cmdline:run']
    }
)
