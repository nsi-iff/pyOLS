from pyols.model import *
from pyols.fonts import findFonts
from pyols.exceptions import PyolsNotFound, PyolsProgrammerError
from pyols.util import create_methods

import difflib
from types import *

def _unifyRawResults(results):
    """ Unify result list and add scores for unique objects.
        Result is list of tuples (score, object).
        results: a list of (relevence, Keyword) tuples.
        >>> _unifyRawResults([(1.0, 'dog'), (1.0, 'cat'), (1.0, 'dog')])
        [(2.0, 'dog'), (1.0, 'cat')]
        >>> """

    result = []
    obs = []
    for (rel, kw) in results:
        if not kw in obs:
            result.append((rel, kw))
            obs.append(kw)
        else:
            index = obs.index(kw)
            result[index] = (result[index][0] + rel, result[index][1])

    return result

def publish(func):
    """ Publish func to the OntologyTool so it will be expored to RPC.
        Unless it is also wrapped in staticmethod, func will be passed
        an instance of the OntologyTool as the first argument when it
        is called by RPC.
        It is very possible that this could result in some tight
        coupling, so use with caution.
        > @publish
        . def checkNamespace(ot)
        .     return ot.namespace == "spam"
        > """
    setattr(OntologyTool, func.__name__, func)
    return func

class OntologyTool(object):
    def __init__(self, namespace):
        # Set the namespace we will use for convinience, but it can be changed
        # using instance.namespace = new_namespace without consequence.
        self.namespace = namespace

        self._fontpath=''
        self._fonts=findFonts()
        self._cutoff = 0.1
        self._gvfont = ''
        self._relfont = ''
        self._forth = '1'
        self._back = '0'
        self._focus_nodeshape = 'ellipse'
        self._focus_nodecolor = '#dee7ec'
        self._focus_node_font_color = '#000000'
        self._focus_node_font_size = 9
        self._first_nodeshape = 'box'
        self._first_nodecolor = '#dee7ec'
        self._first_node_font_color = '#000000'
        self._first_node_font_size = 8
        self._second_nodeshape = 'box'
        self._second_nodecolor = '#dee7ec'
        self._second_node_font_color = '#000000'
        self._second_node_font_size = 7
        self._edgeshape = 'normal'
        self._edgecolor = '#cde2a7'
        self._edge_font_color = '#000000'
        self._edge_font_size = 8
        self._encoding = 'utf-8'

    def _set_namespace(self, new_namespace):
        """ Set the current namespace.
            It it does not exist, it will be created. """
        self._namespace = Namespace.get_or_create_by(name=new_namespace)
        # The namespace is flushed now because there is a good chance
        # other things will depend on it.
        self._namespace.flush()

    def _get_namespace(self):
        """ Return the name of the current namespace. """
        return self._namespace.name
    namespace = property(_get_namespace, _set_namespace)

    # XXX: REFACTOR THIS BIT
    def obj_with_args(obj):
        required = []
        optional = []
        for col in obj.list_columns():
            if col.name == "namespace": continue
            if col.required:
                required.append(col.name)
            else:
                optional.append(str(col.name) + "=" + repr(col.default))
        required = ", ".join(required + optional)
        return (obj, "(" + required + ")")

    # XXX: ADD ERROR CHECKING HERE
    def _generate_query(self, class_, args, kwargs, pk_only=False):
        args = list(args)
        query = {}
        for col in class_.list_columns():
            if pk_only and not col.required: continue

            if col.name == 'namespace':
                query['namespace'] = self._namespace
                continue

            if col.required and args:
                to_add = args.pop(0)
            else:
                if col.name not in kwargs: continue
                to_add = kwargs[col.name]

            if col.type.__module__ == 'pyols.model':
                to_add = self._generic_get(col.type, to_add)
            query[col.name] = to_add
        return query

    @create_methods('add%s', (obj_with_args(Keyword),
                              obj_with_args(KeywordAssociation),
                              obj_with_args(KeywordRelationship)))
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
            will be set to None and the inverse of B set to the new relation. """

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

    @create_methods('get%s', (obj_with_args(Keyword),
                              obj_with_args(Relation),
                              obj_with_args(KeywordAssociation),
                              obj_with_args(KeywordRelationship)))
    def _generic_get(self, class_, *args, **kwargs):
        """ Get a %(class_name)s from the ontology.  It is an
            error to request an item which does not exist. """
        query = self._generate_query(class_, args, kwargs)
        return class_.fetch_by(**query)

    @create_methods('del%s', (obj_with_args(Keyword),
                              obj_with_args(Relation),
                              obj_with_args(KeywordAssociation),
                              obj_with_args(KeywordRelationship)))
    def _generic_del(self, class_, *args, **kwargs):
        """ Remove %(class_name)s, along with all dependencies,
            from the current ontology. """
        i = self._generic_get(class_, *args, **kwargs)
        i.remove()

    @create_methods("query%ss", (obj_with_args(Keyword),
                                 obj_with_args(Relation),
                                 obj_with_args(KeywordAssociation),
                                 obj_with_args(KeywordRelationship)))
    def _generic_query(self, class_, **kwargs):
        """ Return an iterator over all the %(class_name)ss in the current
            namespace matching kwargs.  kwargs may be empty. """
        query = self._generate_query(class_, [], kwargs)
        return class_.query_by(**query)

    def getRelatedKeywords(self, keyword, links=None, cutoff=0.1):
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
        return self._getRelatedKeywords(kw, links, cutoff, 1, {})

    def _getRelatedKeywords(self, kw, links, cutoff, factor, results):
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
            self._getRelatedKeywords(child, links, cutoff, new_factor, results)

        return results

    ###
    # ug... Getters and setters
    ###

    def getFocusNodeShape(self):
        """Return the current gv focus_nodeshape.
        """
        return self._focus_nodeshape

    def setFocusNodeShape(self, focus_nodeshape):
        """Set the focus_nodeshape for gv output.
        """
        self._focus_nodeshape=focus_nodeshape

    def getFocusNodeColor(self):
        """Return the current gv focus_nodecolor.
        """
        return self._focus_nodecolor

    def setFocusNodeColor(self, focus_nodecolor):
        """Set the focus_nodecolor for gv output.
        """
        self._focus_nodecolor=focus_nodecolor

    def getFocusNodeFontColor(self):
        """Return the current gv focus_node_font_color.
        """
        return self._focus_node_font_color

    def setFocusNodeFontColor(self, focus_node_font_color):
        """Set the focus_node_font_color for gv output.
        """
        self._focus_node_font_color=focus_node_font_color

    def getFocusNodeFontColor(self):
        """Return the current gv focus_node_font_color.
        """
        return self._focus_node_font_color

    def setFocusNodeFontColor(self, focus_node_font_color):
        """Set the focus_node_font_color for gv output.
        """
        self._focus_node_font_color=focus_node_font_color

    def getFocusNodeFontSize(self):
        """Return the current gv focus_node_font_size.
        """
        return self._focus_node_font_size

    def setFocusNodeFontSize(self, focus_node_font_size):
        """Set the focus_node_font_size for gv output.
        """
        self._focus_node_font_size=focus_node_font_size

    def getFocusNodeShape(self):
        """Return the current gv focus_nodeshape.
        """
        return self._focus_nodeshape

    def setFocusNodeColor(self, focus_nodeshape):
        """Set the focus_nodeshape for gv output.
        """
        self._focus_nodeshape=focus_nodeshape

    def getFocusNodeColor(self):
        """Return the current gv focus_nodecolor.
        """
        return self._focus_nodecolor

    def setFocusNodeColor(self, focus_nodecolor):
        """Set the focus_nodecolor for gv output.
        """
        self._focus_nodecolor=focus_nodecolor

    def getFocusNodeFontColor(self):
        """Return the current gv focus_node_font_color.
        """
        return self._focus_node_font_color

    def setFocusNodeFontColor(self, focus_node_font_color):
        """Set the focus_node_font_color for gv output.
        """
        self._focus_node_font_color=focus_node_font_color

    def getFocusNodeFontColor(self):
        """Return the current gv focus_node_font_color.
        """
        return self._focus_node_font_color

    def setFocusNodeFontColor(self, focus_node_font_color):
        """Set the focus_node_font_color for gv output.
        """
        self._focus_node_font_color=focus_node_font_color

    def getFocusNodeFontSize(self):
        """Return the current gv focus_node_font_size.
        """
        return self._focus_node_font_size

    def setFocusNodeFontSize(self, focus_node_font_size):
        """Set the focus_node_font_size for gv output.
        """
        self._focus_node_font_size=focus_node_font_size

    def getFirstNodeShape(self):
        """Return the current gv first_nodeshape.
        """
        return self._first_nodeshape

    def setFirstNodeShape(self, first_nodeshape):
        """Set the first_nodeshape for gv output.
        """
        self._first_nodeshape=first_nodeshape

    def getFirstNodeColor(self):
        """Return the current gv first_nodecolor.
        """
        return self._first_nodecolor

    def setFirstNodeColor(self, first_nodecolor):
        """Set the first_nodecolor for gv output.
        """
        self._first_nodecolor=first_nodecolor

    def getFirstNodeFontColor(self):
        """Return the current gv first_node_font_color.
        """
        return self._first_node_font_color

    def setFirstNodeFontColor(self, first_node_font_color):
        """Set the first_node_font_color for gv output.
        """
        self._first_node_font_color=first_node_font_color

    def getFirstNodeFontColor(self):
        """Return the current gv first_node_font_color.
        """
        return self._first_node_font_color

    def setFirstNodeFontColor(self, first_node_font_color):
        """Set the first_node_font_color for gv output.
        """
        self._first_node_font_color=first_node_font_color

    def getFirstNodeFontSize(self):
        """Return the current gv first_node_font_size.
        """
        return self._first_node_font_size

    def setFirstNodeFontSize(self, first_node_font_size):
        """Set the first_node_font_size for gv output.
        """
        self._first_node_font_size=first_node_font_size

    def getSecondNodeShape(self):
        """Return the current gv second_nodeshape.
        """
        return self._second_nodeshape

    def setSecondNodeShape(self, second_nodeshape):
        """Set the second_nodeshape for gv output.
        """
        self._second_nodeshape=second_nodeshape

    def getSecondNodeColor(self):
        """Return the current gv second_nodecolor.
        """
        return self._second_nodecolor

    def setSecondNodeColor(self, second_nodecolor):
        """Set the second_nodecolor for gv output.
        """
        self._second_nodecolor=second_nodecolor

    def getSecondNodeFontColor(self):
        """Return the current gv second_node_font_color.
        """
        return self._second_node_font_color

    def setSecondNodeFontColor(self, second_node_font_color):
        """Set the second_node_font_color for gv output.
        """
        self._second_node_font_color=second_node_font_color

    def getSecondNodeFontColor(self):
        """Return the current gv second_node_font_color.
        """
        return self._second_node_font_color

    def setSecondNodeFontColor(self, second_node_font_color):
        """Set the second_node_font_color for gv output.
        """
        self._second_node_font_color=second_node_font_color

    def getSecondNodeFontSize(self):
        """Return the current gv second_node_font_size.
        """
        return self._second_node_font_size

    def setSecondNodeFontSize(self, second_node_font_size):
        """Set the second_node_font_size for gv output.
        """
        self._second_node_font_size=second_node_font_size

    def getEdgeShape(self):
        """Return the current gv edgeshape.
        """
        return self._edgeshape

    def setEdgeShape(self, edgeshape):
        """Set the edgeshape for gv output.
        """
        self._edgeshape=edgeshape

    def getEdgeColor(self):
        """Return the current gv edgecolor.
        """
        return self._edgecolor

    def setEdgeColor(self, edgecolor):
        """Set the edgecolor for gv output.
        """
        self._edgecolor=edgecolor

    def getEdgeFontColor(self):
        """Return the current gv edge_font_color.
        """
        return self._edge_font_color

    def setEdgeFontColor(self, edge_font_color):
        """Set the edge_font_color for gv output.
        """
        self._edge_font_color=edge_font_color

    def getEdgeFontColor(self):
        """Return the current gv edge_font_color.
        """
        return self._edge_font_color

    def setEdgeFontColor(self, edge_font_color):
        """Set the edge_font_color for gv output.
        """
        self._edge_font_color=edge_font_color

    def getEdgeFontSize(self):
        """Return the current gv edge_font_size.
        """
        return self._edge_font_size

    def setEdgeFontSize(self, edge_font_size):
        """Set the edge_font_size for gv output.
        """
        self._edge_font_size=edge_font_size

    def getGVFontList(self):
        """Return the current gv font list.
        """
        return self._fonts

    def getFontPath(self):
        """Return the saved systems font path.
        """
        return self._fontpath

    def getGVFont(self):
        """Return the current gv font.
        """
        return self._gvfont

    def setGVFont(self, font):
        """Set the font for gv output.
        """
        self._gvfont=font

    def getRelFont(self):
        """Return the current relation font.
        """
        return self._relfont

    def setRelFont(self, font):
        """Set the font for relation output.
        """
        self._relfont=font

    def getBack(self):
        """Return if Back References should be used in the KeywordMap generation.
        """
        return self._back

    def setBack(self, back):
        """Set the back option.
        """
        self._back=back

    def getForth(self):
        """Return if Forward References should be used in the KeywordMap generation.
        """
        return self._forth

    def setForth(self, forth):
        """Set the forth option"""
        self._forth=forth

    def getEncoding(self):
        """Get the encoding of strings used in the classification tool.
        """
        return self._encoding

    def setEncoding(self, encoding):
        """Set the encoding of strings used in the classification tool.
        """
        self._encoding = encoding


if __name__ == '__main__':
    import doctest
    doctest.testmod()
