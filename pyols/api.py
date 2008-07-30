""" Publicly available API for PyOLS. """
from pyols.model import *
from pyols.fonts import findFonts
from pyols.exceptions import PyolsNotFound, PyolsProgrammerError, PyolsException
from pyols.util import create_methods, class_with_args

import difflib
from types import *

__all__ = ['publish', 'OntologyTool']

def publish(func):
    """ Publish 'func' to the OntologyTool so it will be expored to RPC.
        Unless it is also wrapped in staticmethod, func will be passed
        an instance of the OntologyTool as the first argument when it
        is called by RPC.
        When this function is used in a module, it should be imported in
        pyols.__init__ to ensure there are no dependency loops.
        It is very possible that this could result in some tight
        coupling, so use with caution.
        > @publish
        . def checkNamespace(ot)
        .     return ot.namespace == "spam"
        > OntologyTool("spam").checkNamespace()
        True
        > """
    setattr(OntologyTool, func.__name__, func)
    return func

class OntologyTool(object):
    """ All of the methods which will be available over RPC.
        All methods accept primitive types (strings, lists, dictionaries)
        as arguments and do not require the use of kwargs (as they are not
        available over RPC). """
    def __init__(self, namespace):
        # Set the namespace we will use for convinience, but it can be changed
        # using instance.namespace = new_namespace without consequence.
        self.namespace = namespace

    def _set_namespace(self, new_namespace):
        """ Set the current namespace.
            It it does not exist, it will be created. """
        self._namespace = Namespace.get_or_create_by(name=new_namespace)
        # The namespace is flushed now because there is a good chance
        # other things will depend on it.
        self._namespace.flush()
    def _get_namespace(self):
        """ The name of the current namespace. """
        return self._namespace.name
    namespace = property(_get_namespace, _set_namespace)

    def copyNamespace(self, target):
        """ Copy the content of the current namespace to 'target'.
            It is an error if namespace 'target' exists.
            The new namespace is returned. """
        return self._namespace.copy_to(target)

    def _generate_query(self, class_, args, kwargs, \
                        pk_only=False, include_none=True):
        """ Return a dictionary which can be used to query for ``class_``,
            given args and kwargs.  ``pk_only`` and ``include_none``,
            respectively, return only keys which are part of the primary key
            and include values even if they are None.::

            >  _generate_query(Keyword, ['foo', 'bar'], {'description': 'baz'})
            {'namespace': <Namespace ...>,
             'name': 'foo', 'disambiguation': 'bar',
             'description': 'baz'}
            > _generate_query(Keyword, [], {'name': 'foo'})
            {'namespace': <Namespace ...>,
             'name': foo'} """
        # Note: This method does very little error checking -- it might
        #       explode in weird and wonderful ways if it is supplied
        #       with sufficiently poor input.
        args = list(args)
        query = {}
        for field in class_.list_fields():
            if pk_only and not field.required: continue

            if field.name == 'namespace':
                query['namespace'] = self._namespace
                continue

            if field.required and args:
                to_add = args.pop(0)
            else:
                if field.name in kwargs:
                    to_add = kwargs[field.name]
                elif args:
                    to_add = args.pop(0)
                else:
                    continue

            if to_add is None and not include_none:
                continue

            if field.type.__module__ == 'pyols.model':
                to_add = self._generic_get(field.type, to_add)

            query[field.name] = to_add
        return query

    @create_methods('add%s', (class_with_args(Keyword),
                              class_with_args(KeywordAssociation),
                              class_with_args(KeywordRelationship)))
    def _generic_add(self, class_, *args, **kwargs):
        """ Add a %(class_name)s to the ontology.  If an instance already exist,
            it will be updated.  The new instance is returned. """
        query = self._generate_query(class_, args, kwargs, pk_only=True)
        new = class_.get_or_create_by(**query)
        # Call _generate_query again so foreign keys will be resolved
        # to objects on the set.
        for (k, v) in self._generate_query(class_, args, kwargs).items():
            setattr(new, k, v)
        new.assert_valid()
        # Note that assert_unique is not called here because, if the object
        # is not unique, the existing version will be returned.
        return new

    def addRelation(self, name, weight=1.0, types=[],
                    inverse=None, description=u''):
        """ Create a keyword relation 'name'.  If a relation with name 'name'
            already exists, it will be updated with the new values.

            weight is in the range [0,1].
            types is a list of relationship types, each of which is one of:
                {'transitive', 'symmetric', 'functional', 'inversefunctional'}
            inverse is the name of the the inverse relation.  If it does not
            exist, it will be created with the same weight and types.
            
            If the inverse, B, already has an inverse, C, the inverse of C
            will be set to None and the inverse of B set to the new relation.

            addRelation(name, weight=1.0, types=[], inverse=None, description=u''
            """

        if inverse is not None:
            try:
                inverse = self.getRelation(inverse)
            except PyolsNotFound:
                inverse = self.addRelation(inverse, weight, types)
                # This must be flushed here to prevent circular dependency
                # problems when it's set as the inverse of the other relation
                inverse.flush()

        newrel = Relation.get_or_create_by(namespace=self._namespace, name=name)
        newrel.weight=weight
        newrel.types=types
        newrel.description=description
        newrel.assert_valid()
        newrel.flush()
        newrel.inverse = inverse
        return newrel

    @create_methods('get%s', (class_with_args(Keyword),
                              class_with_args(Relation),
                              class_with_args(Namespace),
                              class_with_args(KeywordAssociation),
                              class_with_args(KeywordRelationship)))
    def _generic_get(self, class_, *args, **kwargs):
        """ Get a %(class_name)s from the ontology.  It is an
            error to request an item which does not exist. """
        query = self._generate_query(class_, args, kwargs)
        return class_.fetch_by(**query)

    @create_methods('update%s', (Keyword, Relation, Namespace))
    def _generic_update(self, class_, new_values):
        """ Update a %(class_name)s to the values in dictionary new_values.
            The only value which must be in new_values is 'id'.
            Input values which are dictionaries or lists (with exception of
            Relation.types) will be ignored, and at the moment the namespace
            cannot be changed either (but that's not a technical limitation).
            """
        valid_keys = ('name', 'description', 'weight', 'types', 'inverse',
                      'disambiguation')
        if 'id' not in new_values:
            raise PyolsException("Required field 'id' was not present in %r, "
                                 "which was passed to update%s."
                                 %(new_values, class_.__name__))

        instance = class_.fetch_by(id=new_values['id'])
        for (key, val) in new_values.items():
            if key not in valid_keys: continue
            if key == 'inverse': val = self.getRelation(val)
            setattr(instance, key, val)
        return instance

    @create_methods('del%s', (class_with_args(Keyword),
                              class_with_args(Relation),
                              class_with_args(Namespace),
                              class_with_args(KeywordAssociation),
                              class_with_args(KeywordRelationship)))
    def _generic_del(self, class_, *args, **kwargs):
        """ Remove %(class_name)s, along with all dependencies,
            from the current ontology. """
        i = self._generic_get(class_, *args, **kwargs)
        i.remove()

    @create_methods("query%ss", (class_with_args(Keyword, False),
                                 class_with_args(Relation, False),
                                 class_with_args(Namespace, False),
                                 class_with_args(KeywordAssociation, False),
                                 class_with_args(KeywordRelationship, False)))
    def _generic_query(self, class_, *args, **kwargs):
        """ Return an iterator over all the %(class_name)ss in the current
            namespace which the given query.  The default of all the arguments
            is None, and None can be used in place of a value which should be
            ignored. """
        query = self._generate_query(class_, args, kwargs, include_none=False)
        return class_.query_by(**query)

    def getRelatedKeywords(self, keyword, cutoff=0.1, links=None):
        """ Return all keywords which are related to 'keyword' by
            a weight greater than 'cutoff'.
            'links' is a list of relationship names which should be
                followed, or None for all relationships.
            'cutoff' is the reverence factor below which links will
                no longer be followed.
            > getRelatedKeywords("cat", cutoff=0.25)
            {'animal': 0.5, 'cat': 1.0, 'dog': 0.25} """
        # Because I don't know exactly how pyOLS is going to be used,
        # I am only providing this function for searching.
        # There is no reason not to extend this function or add more.

        kw = self.getKeyword(keyword)
        return self._getRelatedKeywords(kw, cutoff, links, 1, {})

    def _getRelatedKeywords(self, kw, cutoff, links, factor, results):
        """ Helper function to getRelatedKeywords.
            'kw' is an instance of Keyword.
            'links' is a list of Relations, or None for all relations.
            'factor' is the current relevance factor.
            'results' is a dictionary of {kw name:relevence} pairs.
            Return is the same as getRelatedKeywords.  """

        if kw.name in results: return results

        results[kw.name] = factor
        for (child, relation) in kw.relations:
            if not (links is None or relation.name in links):
                continue
            new_factor = relation.weight * factor
            if new_factor < cutoff:
                continue
            self._getRelatedKeywords(child, cutoff, links, new_factor, results)

        return results


from pyols.tests import run_doctests
run_doctests()
