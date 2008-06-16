from setuptools import setup, find_packages
import sys

install_requires = [
    'SQLAlchemy >= 0.3.9',
    'Elixir >= 0.5.2',
    ]

if sys.version_info < (2, 5):
    # Python 2.5 and up comes with sqlite
    install_requires.append('pysqlite >= 2.2')

if 'develop' in sys.argv:
    # Only install testing tools if we're going to run in develop mode
    install_requires.extend([
        'nose >= 0.10.1',
        'pyparsing >= 1.5.0',
    ])

setup(
    name = 'pyOLS',

    version = "0.1a",

    description = 'Python Remote Ontology provides functions for creating, '
                  'searching and graphing ontologies over XML-RPC.',

    long_description = """
    """,

    author = 'David Wolever',
    
    author_email = 'david@wolever.net',
    
    url = '',
    
    install_requires = install_requires,
    
    extras_require = {
    },
    
    dependency_links = [
    ],
    
    packages=find_packages(),

    include_package_data=True,

    package_data={},

    entry_points= {
        'console_scripts':
            ['pyols = pyols.web.cmdline:run']
    }
)
