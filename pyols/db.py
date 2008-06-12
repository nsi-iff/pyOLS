from pyols.exceptions import PyolsProgrammerError
from pyols import config

from elixir import metadata, session, setup_all, drop_all, objectstore

class DatabaseManager:
    def __init__(self, dbString, debug=False):
        """ Create a DatabaseManager connected to dbString,
            where dbString is in the format:
                database://path """
        # In practice, dbString will probably be sqlite:///path/to/db
        metadata.bind = dbString
        metadata.bind.echo = debug
        setup_all()

        self._in_txn = False

    def create_tables(self):
        """ Create all the database tables. """
        setup_all(create_tables=True)

    def drop_tables(self):
        """ Drop all the database tables. """
        # Probably only useful during testing...
        drop_all()
        objectstore.clear()

    def begin_txn(self):
        """ Begin a transaction. """
        if self._in_txn:
            raise PyolsProgrammerError("A transaction is already active; "
                                        "cannot begin a new one.")
        self._txn = session.begin()
        self._in_txn = True
    
    def commit_txn(self):
        """ Commit the transaction. """
        if not self._in_txn:
            raise PyolsProgrammerError("No transaction is active; "
                                        "cannot commit a transaction.")
        self._txn.commit()

    def abort_txn(self):
        """ Abort the transaction. """
        if not self._in_txn:
            raise PyolsProgrammerError("No transaction is active; "
                                        "cannot about a non-existent txn!")
        self._txn.rollback()
        objectstore.clear()


def get_db():
    """ Return a DatabaseManager connected to the database
        defined in config.db.uri. """
    # This method is mostly here to make testing easier
    return DatabaseManager(config.get('db', 'uri'))
