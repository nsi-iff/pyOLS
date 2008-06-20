from pyols.db import db
from pyols.exceptions import PyolsProgrammerError

import nose
from nose.tools import nottest
import sys

def setup_package():
    """ Return a connection to a temporary database, which will be
        destroyed when the script exists.
        The get_db function in pyols.db will also be replaced with a
        function which returns a reference to this db."""
    if not db.connected:
        db.connect("sqlite:///:memory:")

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
