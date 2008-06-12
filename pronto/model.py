""" Model for PROnto. """

from pronto.exceptions import ProntoValueError, ProntoProgrammerError

from elixir import *
from sqlalchemy import UniqueConstraint

class EntityAddons:
    """ A little class to add some useful functionality to Entities. """
    @classmethod
    def get_or_create(cls, **kwargs):
        """ Query for an object, or if it does not exist, create it. """
        obj = cls.get_by(**kwargs)
        if obj: return obj
        return cls(**kwargs)
    
    def assert_unique(self):
        """ Perform a query to ensure that the current instance is unique
            with respect to it's unique constraints (but _NOT_ PK). """
        constraints = [x for x in self.table.constraints
                               if isinstance(x, UniqueConstraint)]

        if len(constraints) > 1:
            raise ProntoProgrammerError(
                    "assert_unique will not behave correctly if there is more "
                    "than one unique constraint on a table.")

        query = {}
        for c in constraints:
            query[c.name] = getattr(self, c.name)

        if self.get_by(**query):
            vals = ", ".join(["=".join(a) for a in query.items()])
            raise ProntoValueError(
                    "An instance of %s already exists with %s."
                    %(self.__class__.__name__, values)


class Namespace(Entity, EntityAddons):
    has_field('id', Integer, primary_key=True)
    has_field('name', Unicode, unique=True)

    using_options(tablename='namespaces')


class Relation(Entity):
    has_field('id', Integer, primary_key=True)
    belongs_to('namespace', of_kind='Namespace')
    has_field('name', String)
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


class Keyword(Entity, EntityAddons):
    has_field('id', Integer, primary_key=True)
    belongs_to('namespace', of_kind='Namespace')

    has_field('name', Unicode)
    has_field('disambiguation', Unicode)
    has_field('description', Unicode)

    has_many('associations', of_kind='KeywordAssociation')
    has_many('left_relations', of_kind='KeywordRelationship', inverse='left')
    has_many('right_relations', of_kind='KeywordRelationship', inverse='right')

    using_options(tablename='keywords')
    using_table_options(UniqueConstraint('namespace_id', 'name', 'disambiguation'))


class KeywordAssociation(Entity):
    has_field('path', Unicode, primary_key=True)
    belongs_to('keyword', of_kind='Keyword', primary_key=True)


class KeywordRelationship(Entity):
    _kws={'primary_key': True, 'ondelete': 'cascade'}
    belongs_to('left', of_kind='Keyword', **_kws)
    belongs_to('relation', of_kind='Relation', **_kws)
    belongs_to('right', of_kind='Keyword', **_kws)
    del _kws

    using_options(tablename='keyword_relationships')
    

metadata.bind = "sqlite:///:memory:"
metadata.bind.echo = True
setup_all(True)
