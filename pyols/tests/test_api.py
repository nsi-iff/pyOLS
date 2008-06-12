from pyols.api import OntologyTool
from pyols.model import Keyword, Namespace
from pyols.tests import run_tests, db
from pyols.exceptions import PyolsNotFound, PyolsValidationError

from nose.plugins.skip import SkipTest
from nose.tools import raises, assert_raises, assert_equal, ok_

class TestOntologyTool:
    def setup(self):
        # ot => OntologyTool
        self.ot = OntologyTool(u"_sanity_check_ns")
        # Add a couple keywords to this other namespace in the
        # hope that this will make it easier to catch problems
        # involving code which ignores the namespace
        self.keyword_new(description=u"In the sanity check NS.")
        self.keyword_new(name=u"testKW2", description=u"In the sanity check NS.")
        self.ot.namespace = u"testNS"

    def teardown(self):
        db().reset()

    def addKeyword(self, name=u"testKW", disambiguation=u"dis",
                   description=u"desc"):
        """ Add a keyword using a call to the OT. """
        self.ot.addKeyword(name, disambiguation, description)
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

    def testDelKeywordCastcadingDelete(self):
        # This will eventually make sure that deletes of keywords
        # castcade to associated relationships and associations
        raise SkipTest("This one will be finished later.")

    def testKeywords(self):
        assert_equal(list(self.ot.keywords()), [])

        for x in range(3):
            self.keyword_new(name=u"testKW%d"%(x))
            kws = list(self.ot.keywords())
            assert_equal(len(kws), x+1)

    def addRelation(self, name=u"testRel", weight=1.0, types=[], inverse=None):
        newRel = self.ot.addRelation(name=name, weight=weight, types=types,
                                     inverse=inverse)
        db().flush() # Simulate a web request -- flush
        return newRel

    def testAddRelation(self):
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

run_tests(__name__)
