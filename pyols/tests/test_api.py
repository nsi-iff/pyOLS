from pyols.api import OntologyTool
from pyols.model import *
from pyols.tests import run_tests, db
from pyols.exceptions import PyolsNotFound, PyolsValidationError

from nose.plugins.skip import SkipTest
from nose.tools import raises, assert_raises, assert_equal, ok_

class TestOntologyTool:
    def setup(self):
        db().begin_txn()
        # ot => OntologyTool
        self.ot = OntologyTool(u"_sanity_check_ns")
        # Add a couple keywords to this other namespace in the
        # hope that this will make it easier to catch problems
        # involving code which ignores the namespace
        self.keyword_new(description=u"In the sanity check NS.")
        self.keyword_new(name=u"testKW2", description=u"In the sanity check NS.")
        self.ot.namespace = u"testNS"

    def teardown(self):
        db().abort_txn()

    def addKeyword(self, name=u"testKW", disambiguation=u"dis",
                   description=u"desc"):
        """ Add a keyword using a call to the OT. """
        self.ot.addKeyword(name, disambiguation=disambiguation,
                           description=description)
        db().flush() # Mimic the flush that hapens at the end of each request

    def checkKeyword(self, kw, name=u"testKW", disambiguation=u"dis",
                     description=u"desc"):
        ok_(kw)
        assert_equal(kw.disambiguation, disambiguation)
        assert_equal(kw.description, description)
        assert_equal(kw.namespace.name, self.ot.namespace)

    def keyword_new(self, name=u"testKW", disambiguation=u"dis",
                    description=u"desc"):
        """ Add a keyword using Keyword.new. """
        kw = Keyword.new(namespace=self.ot._namespace, name=name,
                         disambiguation=disambiguation,
                         description=description)
        kw.flush()
        return kw

    def keyword_getby(self, name=u"testKW"):
        """ Query for a keyword using Keyword.get_by. """
        return Keyword.get_by(name=name, namespace=self.ot._namespace)

    def testChangeNamespace(self):
        nn = u"newNamespace" # nn => newNamespace
        self.ot.namespace = nn
        ok_(Namespace.get_by(name=nn))
        assert_equal(self.ot.namespace, nn)

        # Keywords added should be part of the new namespace
        self.addKeyword()
        k = self.keyword_getby()
        assert_equal(k.namespace.name, nn)

        # And we should be able to go back to the old NS without an issue
        self.ot.namespace = u"testNS"
        assert_equal(self.ot.namespace, "testNS")

    def testAddKeyword(self):
        self.addKeyword()
        k = self.keyword_getby()
        self.checkKeyword(k)

        self.ot.namespace = u"newNamespace"
        # If the namespace hasn't changed,
        # this will raise an exception
        self.addKeyword()

    @raises(PyolsValidationError)
    def testAddDuplicateKeyword(self):
        self.addKeyword()
        self.addKeyword()

    def testGetKeyword(self):
        self.keyword_new()
        k = self.ot.getKeyword(u"testKW")
        self.checkKeyword(k)

        self.ot.namespace = u"newNamespace"
        assert_raises(PyolsNotFound, self.ot.getKeyword, u"testKW")

    @raises(PyolsNotFound)
    def testGetInvalidKeyword(self):
        self.ot.getKeyword(u"bad keyword")

    def testDelKeyword(self):
        self.keyword_new()
        self.ot.delKeyword(u"testKW")
        db().flush()
        # The keyword should not exist
        assert_equal(self.keyword_getby(), None)

    @raises(PyolsNotFound)
    def testDelKeywordDoesntExist(self):
        self.ot.delKeyword(u"IdontExist")

    def testDeletingThings(self):
        # These are not exhaustive tests -- see test_model.py for those
        kw0 = self.keyword_new(u"kw0")
        kw1 = self.keyword_new(u"kw1")
        kw2 = self.keyword_new(u"kw2")
        rel = self.relation_new()
        kwr = KeywordRelationship.new(left=kw0, relation=rel, right=kw1)
        kwa = KeywordAssociation.new(keyword=kw2, path=u"/asdf/123")
        db().flush()

        # Removing the keyword should kill the KWA
        self.ot.delKeyword(kw2.name)
        db().flush()
        assert_equal(KeywordAssociation.get_by(keyword=kw2), None)

        # Deleting the relationship should cause the KWR to be deleted
        # but the keywords should stick around
        self.ot.delRelation(rel.name)
        db().flush()
        ok_(self.keyword_getby(name=kw0.name))
        ok_(self.keyword_getby(name=kw1.name))
        assert_equal(KeywordRelationship.get_by(left=kw0), None)

    def testKeywords(self):
        assert_equal(list(self.ot.queryKeywords()), [])

        for x in range(3):
            self.keyword_new(name=u"testKW%d"%(x))
            kws = list(self.ot.queryKeywords())
            assert_equal(len(kws), x+1)

    def addRelation(self, name=u"testRel", weight=1.0, types=[], inverse=None):
        newRel = self.ot.addRelation(name=name, weight=weight, types=types,
                                     inverse=inverse)
        db().flush() # Simulate a web request -- flush
        return newRel

    def relation_new(self, name=u"testRel"):
        newRel = Relation.new(name=name, namespace=self.ot._namespace)
        db().flush()
        return newRel

    def testRelation(self):
        relA = self.addRelation(name=u"relA")
        relB = self.addRelation(name=u"relB", inverse=relA.name)
        assert_equal(relA, relB.inverse)

        # Ensure that the inverse is properly created
        relC = self.addRelation(name=u"relC", types=['transitive'],
                                weight=0.5, inverse=u"relD")
        relD = self.ot.getRelation(u"relD")
        ok_(relD)
        assert_equal(relD.inverse, relC)
        assert_equal(relD.types, ['transitive'])
        assert_equal(relD.weight, 0.5)

        self.ot.delRelation(u"relD")
        db().flush()
        assert_raises(PyolsNotFound, self.ot.getRelation, name=u"relD")

        assert_equal(set(["relA", "relB", "relC"]),
                     set([r.name for r in self.ot.queryRelations()]))

    @raises(PyolsNotFound)
    def testGetBadRelation(self):
        self.ot.delRelation(u'doesnt_exist')

    @raises(PyolsNotFound)
    def testDelBadRelation(self):
        self.ot.delRelation(u'doesnt_exist')

    def testAddKeywordAssociation(self):
        kw = self.keyword_new()
        self.ot.addKeywordAssociation(kw.name, u'asdf')
        db().flush()

        ka = KeywordAssociation.get_by(path=u'asdf')
        ok_(ka)
        assert_equal(ka.keyword.name, kw.name)

    def testAddKeywordRelationship(self):
        kw0 = self.keyword_new(name=u"kw0")
        kw1 = self.keyword_new(name=u"kw1")
        rel = self.relation_new()
        self.ot.addKeywordRelationship(kw0.name, rel.name, kw1.name)
        db().flush()

        kwr = list(KeywordRelationship.query_by())[0]
        ok_(kwr)
        assert_equal(kwr.left.name, kw0.name)
        assert_equal(kwr.right.name, kw1.name)
        assert_equal(kwr.relation.name, rel.name)

run_tests(__name__)
