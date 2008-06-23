from pyols.tests import setup_test_db

def setup_package():
    # This method is called by nosetests
    setup_test_db()
