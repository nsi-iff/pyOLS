from elixir import metadata, session, setup_all, objectstore

class DatabaseManager:
    def create_tables(self):
        setup_all(create_tables=True)

    def connect(self, dbString, debug=False):
        # Create and populate the database
        metadata.bind = dbString
        metadata.bind.echo = debug
        setup_all()

    def begin_txn(self):
        self._txn = session.begin()
    
    def commit_txn(self):
        self._txn.commit()

    def abort_txn(self):
        self._txn.rollback()
        objectstore.clear()
