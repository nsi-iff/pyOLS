from pyols.db import db
from pyols.exceptions import PyolsProgrammerError

import nose
from nose.tools import nottest
import sys

def setup_test_db():
    """ Setup a database which can be used with any tests involving the DB. """
    if not db.connected:
        db.connect("sqlite:///:memory:", debug=True)
        db.create_tables()

class PyolsDBTest(object):
    """ A class which can be used as a base for all tests involving 
        operations on persistant objects. """
    def setup(self):
        setup_test_db()
        db.begin_txn()

    def teardown(self):
        db.abort_txn()

@nottest
def run_tests(pdb=False):
    caller_locals = sys._getframe(1).f_locals
    (name, file) = map(caller_locals.get, ("__name__", "__file__"))
    if name != "__main__": return
    pdb = pdb and "--pdb-failures" or ""
    nose.main(argv=filter(None, ["nosetests", "-d", pdb, file]))

@nottest
def run_doctests():
    """ Run doctests on the calling module if it's __name__ is __main__ """
    caller_locals = sys._getframe(1).f_locals
    if caller_locals['__name__'] == '__main__':
        import doctest
        doctest.testmod()
