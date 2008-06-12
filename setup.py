from setuptools import setup, find_packages

setup(
    name = 'PROnto',

    version = "",

    description = '',

    long_description = """
    """,
    
    classifiers = [
    ],

    author = '',
    
    author_email = '',
    
    url = '',
    
    install_requires = [
        'SQLAlchemy >= 0.3.9',
        'Elixir >= 0.5.2',
    ],
    
    tests_require = [
        'nose >= 0.10.1',
    ],

    extras_require = {
    },
    
    dependency_links = [
    ],
    
    packages=find_packages(),

    include_package_data=True,

    package_data={},

    entry_points="""
    """,
    )
