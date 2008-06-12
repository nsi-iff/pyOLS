""" Model for PROnto. """

from pronto.exceptions import ProntoValidationError, ProntoProgrammerError
from pronto.owl import isXMLNCName

from elixir import *
from sqlalchemy import UniqueConstraint

class StorageMethods:
    """ This class contains all the methods which each storage class
        should implement. """

    @classmethod
    def get_or_create_by(cls, **kwargs):
        """ Get an instance of the class, or if it does not exist,
            create one.
            **kwargs are the attributes of the class (for instance,
            name or description). """
        obj = cls.get_by(**kwargs)
        if obj: return obj
        return cls.new(**kwargs)

    @classmethod
    def get_by(cls, **kwargs):
        """ Get an instance of the class, given attributes **kwargs.
            >>> n = Namespace.get_by(name='spam')
            >>> Keyword.get_by(namespace=n, name='foo')
            <model.Keyword object at 0x83f730c>
            >>> Keyword.get_by(namespace=n, name='I_dont_exist')
            None
            """
        # NOTE: This method is provided by Elixir, so the code here is
        #       _never executed_.

    @classmethod
    def new(cls, **kwargs):
        """ Create a new object which can be save()'d.
            **kwargs are the attributes of the class. """
        return cls(**kwargs)

    def assert_valid(self):
        """ Assert that the new instance is valid. """

        # Make life a little easier because _most_ classes
        # have a name.
        if hasattr(self, 'name'): self.validate_name()
        self.assert_unique()
        self.has_required_fields()

    def has_required_fields(self):
        """ Assert that all the required fields have been filled out. """
        required_fields = [f.name for f in self.c if not f.nullable]
        for field in required_fields:
            field_val = getattr(self, field)
            if not field_val:
                raise ProntoValidationError(
                        "Field %s of %s null (%r) when it must be non-null"
                        %(field, self, field_val))

    def assert_unique(self):
        """ Raise an exception if the instance is not unique with
            respect to it's unique constraints. """
        constraints = [x for x in self.table.constraints
                               if isinstance(x, UniqueConstraint)]

        if len(constraints) > 1:
            raise ProntoProgrammerError(
                    "assert_unique will not behave correctly if there is more "
                    "than one unique constraint on a table.")

        query = {}
        for col in constraints[0].columns.keys():
            query[col] = getattr(self, col)

        if self.get_by(**query):
            vals = ", ".join(["=".join(a) for a in query.items()])
            raise ProntoValidationError(
                    "A %s already exists with %s."
                    %(self.__class__.__name__, values))

    def validate_name(self):
        # This may or may not stay here... I need to figure out how to
        # do validateion.
        if not hasattr(self, 'name'):
            raise ProntoProgrammerError("%s does not have a name."
                                        %(self.__class__.__name__))

        if not isXMLNCName(self.name):
            raise ProntoValidationError("%s is not a valid name for a %s"
                                        %(self.name, self.__class__.__name__))

    def save(self):
        """ "Save" this instance, making it persistant.
            Does not nessicarly guarentee that the object will "hit the disk"
            right away -- just that, at some point, it will. """
        self.flush()


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
    has_field('name', Unicode, unique=True, required=True)

    using_options(tablename='namespaces')


"""
Relations are the different possible ways keywords can be connected.
  For example, relations "synonymOf", "childOf" and "parentOf" will
  probably exist.

Relations bind keywords together through "KeywordRelationship"s.
"""
class Relation(Entity):
    has_field('id', Integer, primary_key=True)
    belongs_to('namespace', of_kind='Namespace', required=True)
    has_field('name', String, required=True)

    has_field('revelance', Float, default=1)
    has_field('transitive', Boolean, default=False)
    has_field('symmetric', Boolean, default=False)
    has_field('functional', Boolean, default=False)
    has_field('inverse_functional', Boolean, default=False)
    belongs_to('inverse', of_kind='Relation')
    # The 'belongs_to' is slightly misleading here... But
    # it's the best way to express this kind of relationship

    using_options(tablename='relations')
    using_table_options(UniqueConstraint('namespace_id', 'name'))


class Keyword(Entity, StorageMethods):
    has_field('id', Integer, primary_key=True)
    belongs_to('namespace', of_kind='Namespace', required=True)
    has_field('name', Unicode, required=True)

    has_field('disambiguation', Unicode, default='')
    has_field('description', Unicode, default='')

    has_many('associations', of_kind='KeywordAssociation')
    has_many('left_relations', of_kind='KeywordRelationship', inverse='left')
    has_many('right_relations', of_kind='KeywordRelationship', inverse='right')

    using_options(tablename='keywords')
    using_table_options(UniqueConstraint('namespace_id', 'name', 'disambiguation'))

class KeywordAssociation(Entity):
    has_field('path', Unicode, primary_key=True)
    belongs_to('keyword', of_kind='Keyword', primary_key=True)
    
    using_options(tablename='keyword_associations')

class KeywordRelationship(Entity):
    belongs_to('left', of_kind='Keyword', primary_key=True)
    belongs_to('relation', of_kind='Relation', primary_key=True)
    belongs_to('right', of_kind='Keyword', primary_key=True)

    using_options(tablename='keyword_relationships')
    

metadata.bind = "sqlite:///:memory:"
metadata.bind.echo = True
setup_all(True)
