""" Model for PROnto. """

from elixir import *
from sqlalchemy import UniqueConstraint

class Relation(Entity):
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

class Keyword(Entity):
    has_field('name', Unicode)
    has_field('association', Unicode)
    has_many('relations', of_kind='Relation')

    using_options(tablename='keywords')
    using_table_options(UniqueConstraint('namespace_id', 'name', 'association'))

class Namespace(Entity):
    has_field('name', Unicode)
