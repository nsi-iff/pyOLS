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
    'Schevo >= 3.1a1',
    ],
    
    tests_require = [
    'nose >= 0.10.1',
    ],

    test_suite = 'nose.collector',

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
