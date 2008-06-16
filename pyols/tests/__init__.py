from pyols.db import DatabaseManager
from pyols.exceptions import PyolsProgrammerError

import nose
from nose.tools import nottest
import sys

_db = None
def setup_package():
    """ Return a connection to a temporary database, which will be
        destroyed when the script exists.
        The get_db function in pyols.db will also be replaced with a
        function which returns a reference to this db."""
    global _db
    _db = DatabaseManager.get_instance("sqlite:///:memory:")
    _db.create_tables()

def db():
    return _db

@nottest
def run_tests(pdb=False):
    caller_locals = sys._getframe(1).f_locals
    (name, file) = map(caller_locals.get, ("__name__", "__file__"))
    if name != "__main__": return
    pdb = pdb and "--pdb-failures" or ""
    nose.main(argv=filter(None, ["nosetests", "-d", pdb, file]))
