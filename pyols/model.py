""" Model for pyOLS. """

from pyols.exceptions import *
from pyols.owl import isXMLNCName

from elixir import *
from sqlalchemy import UniqueConstraint
from itertools import chain

class StorageMethods:
    """ This class contains all the methods which each storage class
        should implement. """

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
        """ Assert that the new instance is valid. """
        self.assert_unique()
        self.has_required_fields()

    def has_required_fields(self):
        """ Assert that all the required fields have been filled out. """
        required_fields = [f.name for f in self.c if not f.nullable]
        for field in required_fields:
            # The ID field is set automatically and can be ignored
            # The endswith test is because linked objects may have IDs too
            # (eg, namespace_id)
            if field.endswith('id'): continue
            field_val = getattr(self, field)
            if not field_val:
                raise PyolsValidationError(
                        "Field %s of %s null (%r) when it must be non-null"
                        %(field, self, field_val))

    def assert_unique(self):
        """ Raise an exception if the instance is not unique with
            respect to it's unique constraints.
            NOTE: This does not check for PK constraints (see #12). """
        constraints = [x for x in self.table.constraints
                               if isinstance(x, UniqueConstraint)]

        if len(constraints) > 1:
            raise PyolsProgrammerError(
                    "assert_unique will not behave correctly if there is more "
                    "than one unique constraint on a table.")

        if not constraints:
            # There are no unique constraints.
            return

        query = {}
        for col in constraints[0].columns.keys():
            query[col] = getattr(self, col)

        if self.get_by(**query):
            vals = ", ".join(["=".join(map(str, a)) for a in query.items()])
            raise PyolsValidationError(
                    "A %s already exists with %s."
                    %(self.__class__.__name__, vals))

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

"""
Namespaces are primarly used to separate ontologies.  For example,
  keyword "foo" can be added to namespace "ontology0" and namespace
  "ontology1" without error.

Some possible uses:
    * Namespaces like plone-pending and plone-accepted could be used with
      PloneOntology to separate pending and accepted parts of an ongology.
    * A tool could present a "beta" namespace in addition to the "production"
      namespace, allowing review of the "beta" namespace before it is
      promoted to "production".

Assumptions:
    * Namespaces are cheep -- it should be very easy to add and remove them
    * Deletes should cascade -- when a namespace dissapears, so should all
      it's "children"
"""
class Namespace(Entity, StorageMethods):
    has_field('id', Integer, primary_key=True)
    has_field('name', Unicode(128), unique=True, required=True)

    using_options(tablename='namespaces')


"""
Relations are the different possible ways keywords can be connected.
  For example, relations "synonymOf", "childOf" and "parentOf" will
  probably exist.

Relations bind keywords together through "KeywordRelationship"s.
"""
class Relation(Entity, StorageMethods):
    has_field('id', Integer, primary_key=True)
    belongs_to('namespace', of_kind='Namespace', required=True)
    has_field('name', Unicode(128), required=True)

    has_field('revelance', Float, default=1)
    has_many('_types', of_kind='RelationType')
    # Note: the original documentation suggested that a relation could
    #       have more than one inverse.  After much though on the matter,
    #       we have decided that this does not make any sense, so we have
    #       left that out.
    belongs_to('_inverse', of_kind='Relation')
    # The 'belongs_to' is slightly misleading here... But
    # it's the best way to express this kind of relationship

    using_options(tablename='relations')
    using_table_options(UniqueConstraint('namespace_id', 'name'))

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
            type = RelationType.new(name=type)
            type.assert_valid()
            self._types.append(type)
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

         
class RelationType(Entity, StorageMethods):
    has_field('name', Integer, primary_key=True)
    belongs_to('relation', of_kind='Relation', primary_key=True)

    using_options(tablename='relation_types')

    valid_types = ('transitive', 'symmetric', 'functional', 'inverse_functional')

    def assert_valid(self):
        if self.name not in self.valid_types:
            raise PyolsValidationError("%s is not a valid relation type. "
                                       "Valid types are %s." \
                                       %(self.name, ", ".join(self.valid_types)))
        StorageMethods.assert_valid(self)

    def remove(self):
        """ Remove this type. """
        self.delete()


class Keyword(Entity, StorageMethods):
    has_field('id', Integer, primary_key=True)
    belongs_to('namespace', of_kind='Namespace', required=True)
    has_field('name', Unicode(128), required=True)

    has_field('disambiguation', UnicodeText, default='')
    has_field('description', UnicodeText, default='')

    has_many('associations', of_kind='KeywordAssociation')
    has_many('left_relations', of_kind='KeywordRelationship', inverse='left')
    has_many('right_relations', of_kind='KeywordRelationship', inverse='right')

    using_options(tablename='keywords')
    using_table_options(UniqueConstraint('namespace_id', 'name', 'disambiguation'))

    def remove(self):
        """ Remove the keyword, along with all KeywordRelationships and
            KeywordAssociations to which it belongs. """
        for d in chain(self.right_relations,
                       self.left_relations,
                       self.associations):
            # Delete each dependency that is associated with this KW
            d.remove()
        self.delete()


class KeywordAssociation(Entity):
    belongs_to('keyword', of_kind='Keyword', primary_key=True)
    has_field('path', Unicode(512), primary_key=True)
    
    using_options(tablename='keyword_associations')

class KeywordRelationship(Entity, StorageMethods):
    belongs_to('left', of_kind='Keyword', primary_key=True)
    belongs_to('relation', of_kind='Relation', primary_key=True)
    belongs_to('right', of_kind='Keyword', primary_key=True)

    using_options(tablename='keyword_relationships')

    def remove(self):
        """ Remove this relationship. """
        self.delete()
