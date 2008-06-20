from pyols.exceptions import PyolsProgrammerError
from pyols import config

from elixir import metadata, session, setup_all, drop_all, objectstore

class DatabaseManager:
    def __init__(self):
        self.connected = False

    def connect(self, dbString, debug=False):
        """ Connect to the database described by 'dbString'.
            Debug enables verbose SQL debugging.
            It is (probably) an error to `connect()` twice. """
        # In practice, dbString will probably be sqlite:///path/to/db
        self._dbString = dbString
        self._debug = debug
        self._txn = None
        metadata.bind = dbString
        metadata.bind.echo = debug
        setup_all()
        self.connected = True

    def create_tables(self):
        """ Create all the database tables. """
        setup_all(create_tables=True)

    def reset(self):
        """ Clean out and reset the database. """
        # Probably only useful during testing...
        objectstore.clear()
        drop_all()
        setup_all(create_tables=True)

    def begin_txn(self):
        """ Begin a transaction. """
        if self._txn:
            raise PyolsProgrammerError("A transaction is already active; "
                                        "cannot begin a new one.")
        self._txn = session.begin()
    
    def commit_txn(self):
        """ Commit the transaction. """
        if not self._txn:
            raise PyolsProgrammerError("No transaction is active; "
                                        "cannot commit a transaction.")
        self._txn.commit()
        self._txn = None

    def abort_txn(self):
        """ Abort the transaction. """
        if not self._txn:
            raise PyolsProgrammerError("No transaction is active; "
                                        "cannot about a non-existent txn!")
        self._txn.rollback()
        self._txn = None
        objectstore.clear()

    def flush(self):
        """ Flush all changes made to persistant objects to disk.
            This includes both new, modified and removed objects. """
        objectstore.flush()

db = DatabaseManager()
