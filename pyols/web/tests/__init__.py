from pyols.tests import get_temp_db

def setup_package():
    global db
    db = get_temp_db()

def reset_db():
    db.drop_tables()
    db.create_tables()
