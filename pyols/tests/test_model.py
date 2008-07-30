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

    def test__rpc__(self):
        # The __rpc__ method of Relation should return 'types' as a list
        # of strings and should have an 'inverse' instead of '_inverse'
        rel = Relation.new(name=u'foo', types=['symmetric'])        
        rel._inverse = rel
        rpc = rel.__rpc__(1)
        assert_equal(rpc['types'], ['symmetric'])
        assert_equal(rpc['inverse'], rel)


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
        self.add_data()

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
        ns = Namespace.new(name=u'testns')
        for rel in Relation.default_relations:
            assert Relation.get_by(namespace=ns, name=rel)

    def testCopy(self):
        self.add_data()
        
        ########## HERE BE DRAGONS! ##########
        # See comments in the copy_to method...
        from sqlalchemy import select, func, and_
        from elixir import session
        sel = lambda *args: select(*args).execute().fetchall()
        # Strip the ID and Namespace from Relations and Keywords
        noid = lambda rs: set([r[2:] for r in rs])

        from pyols import model
        storage_classes = [getattr(model, cls) for cls in model.__all__
                           if cls not in ('Namespace', 'StorageMethods')]

        expected = {}
        for cls in storage_classes:
            expected[cls] = set(sel(cls.table.c))

        for ns in (u'new_ns0', u'new_ns1'):
            ns = self.ns.copy_to(ns)
            
            # Ensure that these have been coppied over
            for cls in (Relation, Keyword):
                instances = set(sel(cls.table.c, cls.namespace_id == ns.id))
                assert_equal(noid(expected[cls]), noid(instances))

            # Note: This is _not_ a complete test -- it will only check
            #       that the same _number_ of items exist -- not that they
            #       are identical.  This is definatly incorrect, but I can't
            #       think of a simple way to make it better... So this is how
            #       it will remain.  Unless you want to fix it :)
            for cls, fk, fk_type in ((KeywordAssociation, 'keyword', Keyword),
                                     (KeywordRelationship, 'left', Keyword),
                                     (RelationType, 'relation', Relation)):
                query = and_(fk_type.id == getattr(cls, fk + '_id'),
                             fk_type.namespace_id==ns.id)
                instances = sel(cls.table.c, query)
                assert_equal(len(instances), len(expected[cls]))

    @raises(PyolsValidationError)
    def testInvalidCopy(self):
        ns = Namespace.new(name=u'testns')
        ns.flush()
        ns.copy_to(u'testns')


class TestStorageMethods:
    def test_list_fields(self):
        kw_fields = Keyword.list_fields()
        expected = [('namespace', None, Namespace, True),
                    ('name', None, unicode, True),
                    ('disambiguation', u'', unicode, False),
                    ('description', u'', unicode, False),
                    ('associations', None, KeywordAssociation, False),
                    ('left_relations', None, KeywordRelationship, False),
                    ('right_relations', None, KeywordRelationship, False)]

        for (id, field) in enumerate(kw_fields):
            for (name, val) in zip(('name', 'default', 'type', 'required'),
                                    expected[id]):
                field_val = getattr(field, name)
                assert_equal(val, field_val,
                             "Error on field %s: %s: %s != %s."
                              %(field.name, name, field_val, val))

    def test__rpc__(self):
        ns = Namespace(name="ns")
        kw = Keyword.new(namespace=ns, name="kw0")
        ka = KeywordAssociation(path="path")
        kw.associations.append(ka)
        expected = {'associations': [ka], 'name': 'kw0', 'left_relations': [],
                    'disambiguation': None, 'right_relations': [],
                    'namespace': ns, 'description': None, 'id': None }
        assert_equal(expected, kw.__rpc__(1))

        # When the depth falls below 1, only the required fields
        # should be present
        expected = {'name': 'kw0', 'namespace': ns, 'id': None }
        assert_equal(expected, kw.__rpc__(0))
        assert_equal(expected, kw.__rpc__(-42))


run_tests()
