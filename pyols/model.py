""" Persistant PyOLS objects. """

from pyols.exceptions import *
from pyols.util import Container

from elixir import *
from sqlalchemy import UniqueConstraint
from itertools import chain

__all__ = ['StorageMethods', 'Namespace', 'Relation', 'RelationType',
           'Keyword', 'KeywordAssociation', 'KeywordRelationship']

class StorageMethods:
    """ Methods used to access persistant objects. """

    @classmethod
    def get_or_create_by(cls, **kwargs):
        """ Get an instance of the class, or if it does not exist,
            create one using new() (note that this means the object
            has _not_ been flush()'d).
            **kwargs are the attributes of the class (for instance,
            name or description). """
        obj = cls.get_by(**kwargs)
        if obj: return obj
        return cls.new(**kwargs)

    @classmethod
    def get_by(cls, **kwargs):
        """ Get an instance of the class, given attributes **kwargs.
            If multiple matching instances exist, the first one is returned.
            >>> n = Namespace.get_by(name='spam')
            >>> Keyword.get_by(namespace=n, name='foo')
            <model.Keyword object at 0x83f730c>
            >>> Keyword.get_by(namespace=n, name='I_dont_exist')
            None
            """
        # NOTE: This method is provided by Elixir, so the code here is
        #       _never executed_.

    @classmethod
    def fetch_by(cls, **kwargs):
        """ Identical to get_by, except an exception is raised if the
            object is not found.
            >>> Keyword.fetch_by(name='bad_name')
            ...
            PyolsNotFound("Keyword with {'name': 'bad_name'} not found.")
            """
        obj = cls.get_by(**kwargs)
        if obj: return obj
        raise PyolsNotFound("%s with %r not found." %(cls.__name__, kwargs))

    @classmethod
    def query_by(cls, **kwargs):
        """ Identical to get_by, except an iterator over all the matching
            instances is returned. """
        return cls.query.filter_by(**kwargs)

    @classmethod
    def new(cls, **kwargs):
        """ Create a new object which can be flush()'d.
            **kwargs are the attributes of the class. """
        return cls(**kwargs)

    def assert_valid(self):
        """ Assert that an instance is valid. """
        self.has_required_fields()

    def has_required_fields(self):
        """ Assert that all the required fields have been filled out. """
        required_fields = [f.name for f in self.list_fields() if f.required]
        for field in required_fields:
            field_val = getattr(self, field)
            if not field_val:
                raise PyolsValidationError(
                        "Field %s of %s is null (%r) when it must be non-null"
                        %(field, self, field_val))

    def assert_unique(self):
        """ Raise an exception if the instance is not unique with
            respect to it's unique constraints.
            NOTE: This does not check for PK constraints. """
        query = {}

        for col in [f.name for f in self.list_fields() if f.required]:
            query[col] = getattr(self, col)

        if self.get_by(**query):
            vals = ", ".join(["=".join(map(str, a)) for a in query.items()])
            raise PyolsValidationError(
                    "A %s already exists with %s."
                    %(self.__class__.__name__, vals))

    @classmethod
    def list_fields(self, include_id=False):
        """ List all the fields in an entity, including their
            names, default values, types and if they are required.
            Returns a list of container objects with attributes.
            If 'include_id' is true, the 'id' field will be included,
            if it exists.
            Note that this does not list the underlying database
            columns -- see 'class.table.c' for that.
            > x = list_fields()[0]
            > x.required
            True
            > x.type
            unicode
            > x.name
            'name' """
        # Note that the order of the returned values is significant
        # Ug.  This is an ugly method.  Sorry :(
        type_map = (('Integer', int), ('Unicode', unicode),
                    ('Float', float))
        cols = []
        for b in self._descriptor.builders:
            if b.name == 'id' and not include_id: continue

            c = Container()
            c.name = b.name
            c.default = b.kwargs.get('default', None)

            if hasattr(b, 'of_kind'):
                col_type = globals()[b.of_kind]
            else:
                for (name, type) in type_map:
                    if name in repr(b.type):
                        col_type = type
            c.type = col_type

            c.required = b.kwargs.get('primary_key', False)\
                         or not b.kwargs.get('nullable', True)\
                         or (hasattr(b, 'column_kwargs')\
                             and (not b.column_kwargs.get('nullable', True)
                                   or b.column_kwargs.get('primary_key', False)))
            cols.append(c)
        return cols

    def flush(self):
        """ Flush this instance to disk, making it persistant.
            In general this method should only be called to resolve
            dependency issues -- if it's possible, it's better to wait
            until the db.flush() is called at the end of each request. """
        # Note: Just like get_by, this method is overriden by Elixir, so
        #       this code here will never get called.

    def remove(self):
        """ Remove the instance from persistant storage.
            This may also involve removing dependant objects.
            Does NOT guarentee that the object or any dependants
            will hit the disk. """
        raise NotImplementedError("This method should be implemented in "
                                  "subclasses so they can clean up any "
                                  "dangling relations. Offending class: "
                                  "%s" %(self.__class__.__name__))

    def __rpc__(self, depth):
        """ Return a dictionary containing each field of the instance. """
        # Note that calling rpcify on the values of the dictionary
        # is up to the caller -- we just return a dictionary.
        return dict([(f.name, getattr(self, f.name)) for f
                     in self.list_fields(include_id=True)
                     if depth > 0 or f.required])


class Namespace(Entity, StorageMethods):
    """ Used to separate ontologies.  For example, keyword "foo" can be added
        to namespace "ontology0" and namespace "ontology1" without error.

        Some possible uses:

            - Namespaces like plone-pending and plone-accepted could be used with
              PloneOntology to separate pending and accepted parts of an ongology.

            - A tool could present a "beta" namespace in addition to the
              "production" namespace, allowing review of the "beta" namespace
              before it is promoted to "production".
 
        Assumptions:

            - Namespaces are cheep -- it should be very easy to add and remove them

            - Deletes should cascade -- when a namespace dissapears, so should all
              it's "children" """
    has_field('id', Integer, primary_key=True)
    name = 'name'
    has_field('name', Unicode(128), unique=True, required=True)

    using_options(tablename='namespaces')

    @classmethod
    def new(cls, default_relations=True, **kwargs):
        n = super(Namespace, cls).new(**kwargs)
        # Note that everything here must be flushed because it
        # may be used in the rest of the query.
        n.assert_valid()
        n.assert_unique()
        n.flush()
        if default_relations:
            for relation in Relation.default_relations:
                Relation.new(namespace=n, name=relation).flush()
        return n

    def copy_to(self, target_name):
        """ Copy all the contents of this namespace to namesapce 'target_name'.
            Namespace 'target_name' must not exist. """

        ##################### WARNING: Here be dragons! #####################
        # I've dropped down to low-level  SQLAlchemy here because it's silly
        # to go through the ORM.  Hopefully the code should be fairly
        # self-explanitory, though... And if not SA is well documented :)
        # Note that the tests use the same sort of code...
        from sqlalchemy import select, func, and_
        from elixir import session
        ex = session.execute
        sel = lambda *args: select(*args).execute().fetchall()
        insert = lambda class_, new: ex(class_.table.insert(), new)

        new_ns = Namespace.new(name=target_name, default_relations=False)
        new_ns.flush()

        # Because we have written some data from the database, SQLite has
        # granted us a write-lock.  See the fifth paragraph of:
        # http://www.sqlite.org/lang_transaction.html
        # This lets us be sure that we can generate sequential IDs like this

        # Primary classes are those which everything else depends on
        primary_classes = (Relation, Keyword)

        # Secondary classes use only the primary classes
        secondary_classes = (KeywordAssociation, KeywordRelationship,
                             RelationType)

        # Get the current maximum id for each "primary" class
        id_map = {}
        for class_ in primary_classes:
            id_map[class_] = {}
            to_add = [] # Instances which will be added after new ids
                        # have been assigned to each instance

            # The 'or 0' is needed because 'None' is returned if
            # no rows exist.
            base_id = (sel([func.max(class_.id)])[0][0] or 0) + 1
            col_names = [c.name for c in class_.table.c]
            # class_.table.c is the list of columns in the class' table
            query = class_.namespace_id==self.id
            for new_id, row in enumerate(sel(class_.table.c, query)):
                new = dict(zip(col_names, row))

                new_id += base_id
                id_map[class_][new['id']] = new_id
                new['id'] = new_id
                new['namespace_id'] = new_ns.id

                if new.get('_inverse_id'):
                    # Don't flush this yet -- wait 'till we're done
                    # to resolve inverses
                    to_add.append(new)
                    continue
                insert(class_, new)

            for new in to_add:
                # Update the _inverse with the new ID
                new['_inverse_id'] = id_map[class_][new['_inverse_id']]
                insert(class_, new)

        for class_ in secondary_classes:
            col_names = [c.name for c in class_.table.c]
            col_types = [c.type for c in class_.list_fields(True)]
            fks = [] # foregn keys
            for (name, type) in zip(col_names, col_types):
                if issubclass(type, primary_classes):
                    fks.append((name, type))

            # Find all the 'class_'s which reference a "primary object"
            # who's namespace is the old namespace.  We only check the
            # first foregn key because it is sufficient.
            query = and_(fks[0][1].id==getattr(class_, fks[0][0]),
                         fks[0][1].namespace_id==self.id)
            for row in sel(class_.table.c, query):
                new = dict(zip(col_names, row))
                for name, type in fks:
                    # Update the foregn key references from the ID map
                    new[name] = id_map[type][new[name]]
                insert(class_, new)
                
        return new_ns


class Relation(Entity, StorageMethods):
    """ Models the different ways Keywords can be related to each other.
        The actual binding is done by the KeywordRelationship class. """
    has_field('id', Integer, primary_key=True)
    # Note that these duplicate definitions are for the benefit of
    # documentation-generating tools -- they don't have any technical purpose.
    namespace = '<Namespace>'
    belongs_to('namespace', of_kind='Namespace', required=True)
    name = '128 characters of unicode'
    has_field('name', Unicode(128), required=True)
    description = 'unicode text'
    has_field('description', UnicodeText, default=u'')

    weight = 'float 0 <= x <= 1'
    has_field('weight', Float, default=1)
    # The delete-orphan is needed for some SQLAlchemy sillyness, even
    # though the _set_types function handles automatically deleting 
    # orphaned types.
    types = 'list of types, eg: ["inverse", "symmetric"]'
    has_many('_types', of_kind='RelationType', cascade='delete-orphan')
    # Note: the original documentation suggested that a relation could
    #       have more than one inverse.  After much though on the matter,
    #       we have decided that this does not make any sense, so we have
    #       left that out.
    inverse = '<Relation>'
    belongs_to('_inverse', of_kind='Relation')
    # The 'belongs_to' is slightly misleading here... But
    # it's the best way to express this kind of relationship

    using_options(tablename='relations')
    using_table_options(UniqueConstraint('namespace_id', 'name'))

    # These relations will be added to every namespace
    default_relations = (u'synonymOf', u'parentOf', u'childOf')

    def _get_inverse(self):
        return self._inverse
    def _set_inverse(self, new_inverse):
        """ Set the inverse of this relationship.
            If the new inverse, B, already has an inverse, C, the inverse of C
            will be set to None and the inverse of B set to self. """

        if new_inverse is None and self.inverse is None:
            # Nothing to do
            return

        if new_inverse is not None and new_inverse._inverse is not None:
            # If the new inverse has an inverse, null it out
            new_inverse._inverse._inverse = None
            new_inverse._inverse.flush()

        if self.inverse is not None:
            # And if we have an inverse, null that out
            self._inverse._inverse = None
            self._inverse.flush()

        if new_inverse is None:
            self._inverse = new_inverse
            return

        if not (new_inverse.id and self.id):
            raise PyolsProgrammerError("Due to ugly issues with circular "
                                       "dependencies, both of the Relations "
                                       "must have an id (ie, been flush()'d "
                                       "before setting the inverse.")
        # First set one side of the inverse ...
        new_inverse._inverse = self
        new_inverse.flush()
        # ... and then the next ...
        self._inverse = new_inverse
        self.flush()
        # ... and everyone is happy :)

    inverse = property(_get_inverse, _set_inverse)

    def _get_types(self):
        return [type.name for type in self._types]
    def _set_types(self, new_types):
        # Make a copy of the new types because we will be modifying it
        new_types = list(new_types)
        # Need to wrap self._types in list(...) because we'll be
        # modifying it during the loop.
        for type in list(self._types):
            if type.name not in new_types:
                self._types.remove(type)
                type.remove()
            else: # The type is in the new_types
                new_types.remove(type.name)

        for type in new_types:
            type = RelationType.new(name=type, relation=self)
            type.assert_valid()
    types = property(_get_types, _set_types)

    def remove(self):
        """ Remove the relation and all dependent KeywordRelationships
            and KeywordTypes. """
        self.inverse = None
        for d in chain(KeywordRelationship.query_by(relation=self),
                       self._types):
            d.remove()
        self.delete()

    def assert_valid(self):
        StorageMethods.assert_valid(self)

        if not 0 <= self.weight <= 1:
            raise PyolsValidationError("%s is not a valid weight for relation %s. "
                                       "Weights must be in the range [0,1]."\
                                       %(self.weight, self.name))

    def __rpc__(self, depth):
        rpc = StorageMethods.__rpc__(self, depth)
        if depth > 0:
            del rpc['_types']
            del rpc['_inverse']
            rpc['types'] = self.types
            rpc['inverse'] = self.inverse
        return rpc


class RelationType(Entity, StorageMethods):
    """ A helper type to allow Relationships to have many types.
        It should never be called directly, or even indirectly -- it should
        be entirely hidden behind the types property on Relationship. """
    has_field('name', Integer, primary_key=True)
    belongs_to('relation', of_kind='Relation', primary_key=True)

    using_options(tablename='relation_types')

    # If a type name isn't in this list, an error will be raised
    valid_types = ('transitive', 'symmetric', 'functional', 'inverse_functional')

    def assert_valid(self):
        if self.name not in self.valid_types:
            raise PyolsValidationError("%s is not a valid relation type. "
                                       "Valid types are %s." \
                                       %(self.name, ", ".join(self.valid_types)))
        StorageMethods.assert_valid(self)

    def remove(self):
        self.delete()


class Keyword(Entity, StorageMethods):
    """ Keeps track of keyword (but not nessicarly instances of keywords)
        in the ontology.

        Keywords can be associated with "real things" in two ways:

          - With the KeywordAssociation class, which creates an association
            between a keyword and a 'path' (which can be any unicode string).
            For example, a keyword association between the path "pyols.model"
            and the keyword "persistant storage".

          - By creating a Keyword with the instance name and an 'instanceOf'
            relationship type, then creating a KeywordRelationship between
            the "instance keyword" and the desitred keyword.
            For example, a KeywordRelationship between keywords "pyols.model"
            and "persistant storage" through relationship "instanceOf".
            The disadvantage of this method is that there is no way (yet) to
            differenciate between keywords which are an 'instance' and keywords
            which are "actually keywords"."""

    # Note that these duplicate definitions are for the benefit of
    # documentation-generating tools -- they don't have any technical purpose.
    has_field('id', Integer, primary_key=True)
    namespace = '<Namespace>'
    belongs_to('namespace', of_kind='Namespace', required=True)
    name = '128 unicode characters'
    has_field('name', Unicode(128), required=True)
    disambiguation = '128 unicode characters'
    has_field('disambiguation', Unicode(128), default=u'')

    description = 'unicode text'
    has_field('description', UnicodeText, default=u'')

    associations = '[<KeywordAssociation(self, "path...")>, ...]'
    has_many('associations', of_kind='KeywordAssociation')
    left_relations = '[<KeywordRelationship(self, '\
                      '<Relationship>, <Keyword>), ...]'
    has_many('left_relations', of_kind='KeywordRelationship', inverse='left')
    right_relations = '[<KeywordRelationship(<Keyword>, '\
                       '<Relationship>, self), ...]'
    has_many('right_relations', of_kind='KeywordRelationship', inverse='right')

    using_options(tablename='keywords')
    using_table_options(UniqueConstraint('namespace_id', 'name', 'disambiguation'))

    @property
    def relations(self):
        """ Yield (keyword, relation) pairs for each keyword
            that is related to this one. 
            Note that they are not nessicarly unique (that is,
            if A relates to B through R, and B relates to A
            through R, two (B, R) tuples will be yielded. """
        for kwr in self.left_relations:
            yield (kwr.right, kwr.relation)
        for kwr in self.right_relations:
            yield (kwr.left, kwr.relation)

    def remove(self):
        """ Remove the keyword, along with all KeywordRelationships and
            KeywordAssociations to which it belongs. """
        for d in chain(self.right_relations,
                       self.left_relations,
                       self.associations):
            # Delete each dependency that is associated with this KW
            d.remove()
        self.delete()


class KeywordAssociation(Entity, StorageMethods):
    """ Used to assocate Keywords with "real things" (instances).
        For an example of how they are used, see the documentation
        on the Keyword class. """
    keyword = '<Keyword>'
    belongs_to('keyword', of_kind='Keyword', primary_key=True)
    path = '512 unicode characters'
    has_field('path', Unicode(512), primary_key=True)
    descrption = 'unicode text'
    has_field('description', UnicodeText, default=u'')
    
    using_options(tablename='keyword_associations')

    def remove(self):
        self.delete()


class KeywordRelationship(Entity, StorageMethods):
    """ Used to bind keywords together.
        For example, keyword "dog" might be bound to keyword "animal"
        though relation "kind of". """
    left = '<Keyword>'
    belongs_to('left', of_kind='Keyword', primary_key=True)
    relation = '<Relation>'
    belongs_to('relation', of_kind='Relation', primary_key=True)
    right = '<Keyword>'
    belongs_to('right', of_kind='Keyword', primary_key=True)

    using_options(tablename='keyword_relationships')

    def remove(self):
        self.delete()
