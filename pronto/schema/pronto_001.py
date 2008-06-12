"""Schema for PROnto."""

from schevo.schema import *
schevo.schema.prep(locals())


class Relation(E.Entity):
    """Stores information about relationships. """
    name = f.string(required=True)
    revelance = f.float(min_value=0, max_value=1, default=1)
    transitive = f.boolean(default=False)
    symmetric = f.boolean(default=False)
    functional = f.boolean(default=False)
    inverse_functional = f.boolean(default=False)
    inverse_of = f.entity('Relation', required=False)

    _key(name)

class Keyword(E.Entity):
    name = f.string(required=True)
    association = f.string(required=True)

    _key(name)
    _index(association)

class KeywordRelationship(E.Entity):
    left = f.entity('Keyword', on_delete=CASCADE)
    relates_by = f.entity('Relation', on_delete=CASCADE)
    right = f.entity('Keyword', on_delete=CASCADE)

    _key(left, relates_by, right)

E.Relation._sample = (
    ( 'parentOf', DEFAULT, DEFAULT, True, DEFAULT, DEFAULT, DEFAULT),
    ( 'childOf', DEFAULT, DEFAULT, True, DEFAULT, DEFAULT, DEFAULT),
)

E.Keyword._sample = (
    ( 'foo', ),
    ( 'bar', ),
)

E.KeywordRelationship._sample = (
    ( ('foo', ), ('parentOf', ), ('bar', )),
    ( ('bar', ), ('childOf', ), ('foo', )),
)

