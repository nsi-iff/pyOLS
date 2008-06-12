from pyols.db import DatabaseManager, get_db

import nose
from nose.tools import nottest

def get_temp_db():
    """ Return a connection to a temporary database, which will be
        destroyed when the script exists.
        The get_db function in pyols.db will also be replaced with a
        function which returns a reference to this db."""
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    # override get_db so it will return this DB all the time
    get_db = lambda: db
    return db

def setup_package():
    global db
    db = get_temp_db()

def reset_db():
    db.drop_tables()
    db.create_tables()

@nottest
def run_tests(name, pdb=False):
    """ Where name is the caller's __name__. """
    if name != "__main__": return
    pdb = pdb and "--pdb-failures" or ""
    nose.main(argv=["", "-d", pdb])
