""" Model for PROnto. """

from elixir import *
from sqlalchemy import UniqueConstraint

class Namespace(Entity):
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


class Keyword(Entity):
    has_field('id', Integer, primary_key=True)
    belongs_to('namespace', of_kind='Namespace')
    has_field('name', Unicode)
    has_field('association', Unicode)

    has_many('left_relations', of_kind='KeywordRelationship', inverse='left')
    has_many('right_relations', of_kind='KeywordRelationship', inverse='right')

    using_options(tablename='keywords')
    using_table_options(UniqueConstraint('namespace_id', 'name', 'association'))


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
