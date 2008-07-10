from pyols.model import *
from pyols.tests import run_tests, db, PyolsDBTest
from pyols.exceptions import PyolsValidationError

from nose.plugins.skip import SkipTest
from nose.tools import raises, assert_raises, assert_equal, ok_

class TestRelation(PyolsDBTest):
    def setup(self):
        super(TestRelation, self).setup()
        self.ns = Namespace.new(name=u"testNS")
        self.ns.flush()

    def relation_new(self, name=u"testRel", weight=1.0, types=[], inverse=None):
        r = Relation.new(namespace=self.ns, name=name, weight=weight,
                         types=types, inverse=inverse)
        r.flush()
        return r

    def testSetInverse(self):
        relA = self.relation_new(name=u"relA")
        relB = self.relation_new(name=u"relB")
        relC = self.relation_new(name=u"relC")
        relD = self.relation_new(name=u"relD")
        db.flush()

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
                    ('inverse_functional', 'transitive'),
                    [])
        for check in to_check:
            db.flush() # Pretend we're in a web request
            rel.types = check
            # Make sure that we can flush the relation here
            # (ie, that there are no broken references from types)
            rel.flush()
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

    def testValid(self):
        def new(weight):
            return Relation.new(name=u"testRel", namespace=self.ns,
                                weight=weight)

        # These should explode
        for weight in (-1, 4):
            rel = new(weight)
            assert_raises(PyolsValidationError, rel.assert_valid)

        # These are all valid
        for weight in (0, 1, 0.5):
            rel = new(weight)
            rel.assert_valid()

    def testRemove(self):
        # Make sure a "naked" relation with no dependencies works
        for types in ([], ['transitive', 'symmetric']):
            rel = self.relation_new(types=types)
            rel.remove()
            db.flush()

        rel = self.relation_new(types=['transitive', 'symmetric'])
        kw0 = Keyword.new(namespace=self.ns, name=u"kw0")
        kw1 = Keyword.new(namespace=self.ns, name=u"kw1")
        kwr = KeywordRelationship.new(left=kw0, relation=rel, right=kw1)
        db.flush()

        rel.remove()
        db.flush()

        # No instances of these types should exist...
        empty_types = (KeywordRelationship, RelationType)
        for type in empty_types:
            assert_equal(list(type.query_by()), [])

        assert_equal(len(list(Relation.query_by())),
                     len(Relation.default_relations))

        # ... but the two keywords should remain.
        assert_equal(set([kw.name for kw in Keyword.query_by()]),
                     set(["kw0", "kw1"]))


class TestRelationType:
    def testValid(self):
        r = Relation.new(namespace=Namespace.new(name=u"foo"), name=u"foo")
        for invalid in ('asdf', '', 'symetric'):
            # Note the misspelling   ^^^^^^^^
            # That is intentional :)
            assert_raises(PyolsValidationError,
                          RelationType.new(name=invalid, relation=r)\
                          .assert_valid)

        for valid in RelationType.valid_types:
            RelationType.new(name=valid, relation=r).assert_valid()


class TestKeyword(PyolsDBTest):
    def setup(self):
        super(TestKeyword, self).setup()
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
        db.flush()

    def testRelations(self):
        assert_equal(sorted(self.kw0.relations),
                     sorted([(self.kw1, self.rel0),
                             (self.kw1, self.rel1),
                             (self.kw1, self.rel0)]))

    def testRemove(self):
        self.kw0.remove()
        db.flush()
        
        # No KeywordRelationships should be left
        assert_equal(len(list(KeywordRelationship.query_by())), 0)
        # And one KeywordAssociation is left
        assert_equal(len(list(KeywordAssociation.query_by())), 1)

        self.kw2.remove()
        db.flush()
        assert_equal(len(list(KeywordAssociation.query_by())), 0)
        
        # And only one keyword
        assert_equal(len(list(Keyword.query_by())), 1)


class TestNamespace(PyolsDBTest):
    def testNewNamespace(self):
        # New namespaces should come pre-loaded with all
        # the default realtions
        ns = Namespace.new(name=u'asdf')
        for rel in Relation.default_relations:
            assert Relation.get_by(namespace=ns, name=rel)

    def testClone(self):
        ns = Namespace.new(name=u'asdf')


class TestStorageMethods:
    def test_list_columns(self):
        kw_cols = Keyword.list_columns()
        expected = [('namespace', None, Namespace, True),
                    ('name', None, unicode, True),
                    ('disambiguation', u'', unicode, False),
                    ('description', u'', unicode, False),
                    ('associations', None, KeywordAssociation, False),
                    ('left_relations', None, KeywordRelationship, False),
                    ('right_relations', None, KeywordRelationship, False)]

        for (id, col) in enumerate(kw_cols):
            for (name, val) in zip(('name', 'default', 'type', 'required'),
                                    expected[id]):
                col_val = getattr(col, name)
                assert_equal(val, col_val,
                             "Error on col %s: %s: %s != %s."
                              %(col.name, name, col_val, val))

    def test__rpc__(self):
        ns = Namespace(name="ns")
        kw = Keyword.new(namespace=ns, name="kw0")
        ka = KeywordAssociation(path="path")
        kw.associations.append(ka)
        expected = {'associations': [ka], 'name': 'kw0', 'left_relations': [],
                    'disambiguation': None, 'right_relations': [],
                    'namespace': ns, 'description': None, 'id': None }
        assert_equal(expected, kw.__rpc__())

run_tests()
