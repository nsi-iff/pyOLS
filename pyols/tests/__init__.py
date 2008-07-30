from pyols.db import db
from pyols.exceptions import PyolsProgrammerError

import nose
from nose.tools import nottest
import sys

def setup_test_db():
    """ Setup a database which can be used with any tests involving the DB.
        It is assumed that calling this functions has no side-effects and
        no cleanup (eg, deleting files) is required afterwards. """
    if not db.connected:
        db.connect("sqlite:///:memory:", debug=False)
        db.create_tables()

class PyolsDBTest(object):
    """ A class which can be used as a base for all tests involving 
        operations on persistant objects. """
    def setup(self):
        setup_test_db()
        db.begin_txn()

    def teardown(self):
        db.abort_txn()

    def add_data(self):
        from pyols.model import *
        ns = Namespace(name=u"testns")
        for kw in (u"kw0", u"kw1", u"kw2"):
            setattr(self, kw, Keyword.new(name=kw, namespace=ns))
        for rel in (u"rel0", u"rel1"):
            setattr(self, rel, Relation.new(name=rel, namespace=ns))

        self.kwr0 = KeywordRelationship.new(left=self.kw0, relation=self.rel0,
                                           right=self.kw1)
        self.kwr1 = KeywordRelationship.new(left=self.kw0, relation=self.rel1,
                                           right=self.kw1)
        self.kwr2 = KeywordRelationship.new(left=self.kw1, relation=self.rel0,
                                           right=self.kw0)

        self.kwa0 = KeywordAssociation.new(keyword=self.kw0, path=u"kwa0")
        self.kwa1 = KeywordAssociation.new(keyword=self.kw2, path=u"kwa1")
        self.ns = ns
        db.flush()

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
