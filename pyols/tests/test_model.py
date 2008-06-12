from pyols.model import Namespace, Relation
from pyols.tests import run_tests, db

from nose.plugins.skip import SkipTest
from nose.tools import raises, assert_raises, assert_equal, ok_

class TestRelation:
    def setup(self):
        self.ns = Namespace.new(name=u"testNS")
        self.ns.flush()

    def teardown(self):
        db().reset()

    def relation_new(self, name=u"testRel", revelance=1.0, types=[], inverse=None):
        r = Relation.new(namespace=self.ns, name=name, revelance=revelance,
                         types=types, inverse=inverse)
        r.flush()
        return r

    def testSetInverse(self):
        relA = self.relation_new(name=u"relA")
        relB = self.relation_new(name=u"relB")
        relC = self.relation_new(name=u"relC")
        relD = self.relation_new(name=u"relD")
        db().flush()

        relA.inverse = None # Nothing should happen

        relA.inverse = relB
        assert_equal(relA.inverse, relB)
        assert_equal(relB.inverse, relA)

        # Get rid of A's inverse
        relA.inverse = None
        assert_equal(relA.inverse, None)
        assert_equal(relB.inverse, None)

        relA.inverse = relB
        # Change A's inverse to C
        relA.inverse = relC
        assert_equal(relA.inverse, relC)
        assert_equal(relB.inverse, None)
        assert_equal(relC.inverse, relA)

        relA.inverse = relB
        relC.inverse = relD
        # In this case, both B and C have different
        # inverses before they are paired.
        relB.inverse = relC
        assert_equal(relA.inverse, None)
        assert_equal(relB.inverse, relC)
        assert_equal(relC.inverse, relB)
        assert_equal(relD.inverse, None)


    def testSetTypes(self):
        raise Exception("You need to write this test!")

run_tests(__name__)
