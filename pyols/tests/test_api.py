from pyols.api import OntologyTool
from pyols.model import *
from pyols.tests import run_tests, db, PyolsDBTest
from pyols.exceptions import PyolsNotFound, PyolsValidationError

from nose.plugins.skip import SkipTest
from nose.tools import raises, assert_raises, assert_equal, ok_

class TestOntologyTool(PyolsDBTest):
    def setup(self):
        super(TestOntologyTool, self).setup()
        # ot => OntologyTool
        self.ot = OntologyTool(u"_sanity_check_ns")
        # Add a couple keywords to this other namespace in the
        # hope that this will make it easier to catch problems
        # involving code which ignores the namespace
        self.keyword_new(description=u"In the sanity check NS.")
        self.keyword_new(name=u"testKW2", description=u"In the sanity check NS.")
        self.ot.namespace = u"testNS"

    def addKeyword(self, name=u"testKW", disambiguation=u"dis",
                   description=u"desc"):
        """ Add a keyword using a call to the OT. """
        kw = self.ot.addKeyword(name, disambiguation=disambiguation,
                                description=description)
        db.flush() # Mimic the flush that hapens at the end of each request
        return kw

    def keyword_new(self, name=u"testKW", disambiguation=u"dis",
                    description=u"desc"):
        """ Add a keyword using Keyword.new. """
        kw = Keyword.new(namespace=self.ot._namespace, name=name,
                         disambiguation=disambiguation,
                         description=description)
        kw.flush()
        return kw

    def addRelation(self, name=u"testRel", weight=1.0, types=[], inverse=None):
        newRel = self.ot.addRelation(name=name, weight=weight, types=types,
                                     inverse=inverse)
        db.flush() # Simulate a web request -- flush
        return newRel

    def relation_new(self, name=u"testRel", **kwargs):
        newRel = Relation.new(name=name, namespace=self.ot._namespace,
                              **kwargs)
        db.flush()
        return newRel

    def checkKeyword(self, kw, name=u"testKW", disambiguation=u"dis",
                     description=u"desc"):
        ok_(kw)
        assert_equal(kw.disambiguation, disambiguation)
        assert_equal(kw.description, description)
        assert_equal(kw.namespace.name, self.ot.namespace)

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

    def testAdd(self):
        kw0 = self.addKeyword(u"kw0")
        kw1 = self.addKeyword(u"kw1")
        rel = self.relation_new()
        self.ot.addKeywordRelationship(kw0.name, rel.name, kw1.name)
        db.flush()

        kwr = list(KeywordRelationship.query_by())[0]
        ok_(kwr)
        assert_equal(kwr.left.name, kw0.name)
        assert_equal(kwr.right.name, kw1.name)
        assert_equal(kwr.relation.name, rel.name)

        self.ot.namespace = u"new_ns"
        ok_(not self.keyword_getby(u"kw0"))
        self.addKeyword(name=u"kw0")
        ok_(self.keyword_getby(name=u"kw0"))

    def testAddDuplicateInstance(self):
        kw = self.addKeyword()
        kw = self.addKeyword()
        # These should both succeed

        self.ot.addKeywordAssociation(kw.name, u'0')
        db.flush()
        self.ot.addKeywordAssociation(kw.name, u'1')
        db.flush()

        # The original keyword association should have been updated.
        ka = KeywordAssociation.get_by(path=u'1')
        ok_(ka)
        assert_equal(ka.keyword.name, kw.name)

    def testAddRelation(self):
        for rel in self.ot.queryRelations():
            rel.remove()
        # Remove the default relations
        db.flush()

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

        # Test that adding a duplicate relation will cause an update.
        self.addRelation(name=u"relD", weight=0)
        relD = self.ot.getRelation(u"relD")
        assert_equal(relD.inverse, None)
        assert_equal(relD.types, [])
        assert_equal(relD.weight, 0)

        # Tests for removing and querying relations are also snuck in here
        self.ot.delRelation(u"relD")
        db.flush()
        assert_raises(PyolsNotFound, self.ot.getRelation, name=u"relD")

        assert_equal(set(["relA", "relB", "relC"]),
                     set([r.name for r in self.ot.queryRelations()]))

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
        db.flush()
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
        db.flush()

        # Removing the keyword should kill the KWA
        self.ot.delKeyword(kw2.name)
        db.flush()
        assert_equal(KeywordAssociation.get_by(keyword=kw2), None)

        # Deleting the relationship should cause the KWR to be deleted
        # but the keywords should stick around
        self.ot.delRelation(rel.name)
        db.flush()
        ok_(self.keyword_getby(name=kw0.name))
        ok_(self.keyword_getby(name=kw1.name))
        assert_equal(KeywordRelationship.get_by(left=kw0), None)

    def testGenericQuery(self):
        # A simple little test
        assert_equal(list(self.ot.queryKeywords()), [])
        for x in range(3):
            self.keyword_new(name=u"testKW%d"%x, description=u"kwd%d"%x)
            kws = list(self.ot.queryKeywords())
            assert_equal(len(kws), x+1)

        # Before we get any further, check that the definition
        # of Keyword has not chnaged
        assert_equal(Keyword.list_columns()[3].name, 'description')

        assert_equal(len(list(self.ot.queryKeywords(None, None, u'kwd0'))), 1)
        assert_equal(len(list(self.ot.queryKeywords(u'testKW0'))), 1)

    def testGetRelatedKeywords(self):
        rs = {}
        rs['k'] = self.relation_new(u"kind of", weight=0.5, types=['symmetric'])
        rs['s'] = self.relation_new(u"synonym of", weight=1, types=['symmetric'])
        rs['b'] = self.relation_new(u"breed of", weight=0.75)
        kwrs = (("animal", "kind of", "living thing"),
                ("dog", "kind of", "animal"),
                ("cat", "kind of", "animal"),
                ("cachorro", "synonym of", "dog"),
                ("egyptian", "breed of", "cat"),
                ("collie", "breed of", "dog"))
        ks = {}
        for kwr in kwrs:
            for kw in (kwr[0], kwr[2]):
                if kw in ks: continue
                ks[kw] = self.keyword_new(unicode(kw))
            KeywordRelationship.new(left=ks[kwr[0]],
                                    relation=rs[kwr[1][0]],
                                    right=ks[kwr[2]])
        db.flush()

        queries = ((("animal", 0.5, None),
                       {'cat': 0.5, 'living thing': 0.5, 'dog': 0.5,
                        'animal': 1, 'cachorro': 0.5}),
                   (("collie", 0.75, None),
                       {'collie': 1, 'dog': 0.75, 'cachorro': 0.75}),
                   (("collie", 0, None),
                       {'collie': 1, 'living thing': 0.1875,
                        'egyptian': 0.140625, 'dog': 0.75, 'cat': 0.1875,
                        'animal': 0.375, 'cachorro': 0.75}),
                   (("living thing", 0, [u"kind of"]),
                       {'living thing': 1, 'dog': 0.25, 'animal': 0.5,
                        'cat': 0.25}),
                   (("dog", 0, [u"synonym of", u"breed of"]),
                       {'collie': 0.75, 'dog': 1, 'cachorro': 1}),
                  )

        for (query, expected) in queries:
            actual = self.ot.getRelatedKeywords(unicode(query[0]),
                                                cutoff=query[1],
                                                links=query[2])
            assert_equal(actual, expected)

run_tests()
