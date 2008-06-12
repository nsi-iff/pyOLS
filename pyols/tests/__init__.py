from pyols.db import DatabaseManager

def get_temp_db():
    """ Return a connection to a temporary database, which will be
        destroyed when the script exists. """
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    return db
