from pyols.model import Namespace, Relation
from pyols.tests import run_tests, db
from pyols.exceptions import PyolsValidationError

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
        rel = self.relation_new(types=['transitive'])
        assert_equal(rel.types, ['transitive'])
        # Use a tuple (instead of a list) here to ensure
        # that it is not modified by _set_types
        to_check = (('transitive', 'symmetric'),
                    ('functional', ),
                    ('inverse_functional', 'transitive'))
        for check in to_check:
            db().flush() # Pretend we're in a web request
            rel.types = check
            # It's imortant to wrap each one in set(...) because
            # their order is not guarenteed
            assert_equal(set(rel.types), set(check))

    @raises(PyolsValidationError)
    def testSetInvalidTypes(self):
        rel = self.relation_new(types=['transitive'])
        rel.types = ['symmetric', 'invalid_type']

    def testGetTypes(self):
        rel = self.relation_new(types=['transitive', 'symmetric'])
        assert_equal(set(rel.types), set(['transitive', 'symmetric']))

run_tests(__name__)
