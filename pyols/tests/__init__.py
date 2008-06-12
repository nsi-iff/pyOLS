from pyols.db import DatabaseManager, get_db

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
