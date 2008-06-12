from pyols.exceptions import PyolsProgrammerError
from pyols import config

from elixir import metadata, session, setup_all, drop_all, objectstore

class DatabaseManager:
    """ A psudo-singleton class which manages the database connection.
        Unless there is a good reason not to, a db connection should
        be created with DatabaseManager.get_instance(...). """
    _instance = None

    def __init__(self, dbString, debug):
        """ Create a DatabaseManager connected to dbString,
            where dbString is in the format:
                database://path """
        # In practice, dbString will probably be sqlite:///path/to/db
        self._dbString = dbString
        self._debug = debug
        self._txn = None
        metadata.bind = dbString
        metadata.bind.echo = debug
        setup_all()

    @classmethod
    def get_instance(cls, dbString=None, debug=False):
        """ Create a DBManager if one does not exist, or return the
            existing instance.
            If a dbString is not provided, the config setting db.uri
            is used.
            An exception is raised if a dbString is provided and it
            differs from the dbString used in the existing instance. """
        # If you are supplying this method with a dbString, and you're
        # not calling it from test code, you'd better have a good reason...
        if not cls._instance:
            if dbString is None:
                dbString = cls.get('db', 'uri')
            cls._instance = cls(dbString, debug)

        if dbString and cls._instance._dbString != dbString:
            raise PyolsProgrammerError("A DBManager was requested, but there "
                                       "already exists a cached manager "
                                       "connected to a different DB.")
        return cls._instance

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
