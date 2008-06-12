from pyols.db import DatabaseManager
from pyols.exceptions import PyolsProgrammerError

import nose
from nose.tools import nottest

def setup_package():
    """ Return a connection to a temporary database, which will be
        destroyed when the script exists.
        The get_db function in pyols.db will also be replaced with a
        function which returns a reference to this db."""
    db = DatabaseManager.get_instance("sqlite:///:memory:")
    db.create_tables()

def reset_db():
    if DatabaseManager._instance is None:
        raise PyolsProgrammerError("reset_db cannot be called before "
                                   "setup_package!")
    DatabaseManager.get_instance().reset()

@nottest
def run_tests(name, pdb=False):
    """ Where name is the caller's __name__. """
    if name != "__main__": return
    pdb = pdb and "--pdb-failures" or ""
    nose.main(argv=["", "-d", pdb])
