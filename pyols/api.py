from pyols.model import Keyword, Namespace, Relation
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


class OntologyTool(object):
    def __init__(self, namespace):
        # Set the namespace we will use for convinience, but it can be changed
        # using instance.namespace = new_namespace without consequence.
        self.namespace = namespace

        self._fontpath=''
        self._fonts=findFonts()
        self._cutoff = 0.1
        self._use_gv_tool = 0
        self._gvfont = ''
        self._relfont = ''
        self._forth = '1'
        self._back = '0'
        self._nodeshapes = ['box', 'polygon', 'ellipse', 'circle', 'point', 'egg', 'triangle', 'plaintext', 'diamond', 'trapezium', 'parallelogram', 'house', 'pentagon', 'hexagon', 'septagon', 'octagon', 'doublecircle', 'doubleoctagon', 'tripleoctagon', 'invtriangle', 'invtrapezium', 'invhouse', 'Mdiamond', 'Msquare', 'Mcircle', 'rect', 'rectangle', 'none']
        self._edgeshapes = ['box', 'crow', 'diamond', 'dot', 'inv', 'none', 'normal', 'tee', 'vee']
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

    @create_methods('add%s', (Keyword, ))
    def _generic_add(self, class_, *args, **kwargs):
        """ Add a %(class_name)s to the ontology.  It is an error
            to add duplicate items.  The new instance is returned. """
        new = class_.new(namespace=self._namespace, **kwargs)
        new.assert_valid()
        return new

    def addRelation(self, name, weight=1.0, types=[], inverse=None):
        """ Create a keyword relation 'name' in the Plone Relations
            library, raising an exception if it already exists.

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

        newrel = Relation.new(namespace=self._namespace,
                              name=name, weight=weight, types=types)
        newrel.assert_valid()
        newrel.flush()
        newrel.inverse = inverse
        return newrel

    @create_methods('get%s', (Keyword, Relation))
    def _generic_get(self, class_, name):
        """ Get a %(class_name)s from the ontology.  It is an
            error to request an item which does not exist. """
        return class_.fetch_by(name=name, namespace=self._namespace)

    @create_methods('del%s', (Keyword, Relation))
    def _generic_del(self, class_, name):
        """ Remove %(class_name)s, along with all dependencies,
            from the current ontology. """
        i = self._generic_get(class_, name=name)
        i.remove()

    @create_methods("query%ss", (Keyword, Relation))
    def _generic_query(self, class_, **kwargs):
        """ Return an iterator over all the %(class_name)ss in the current
            namespace matching kwargs.  kwargs may be empty. """
        return class_.query_by(namespace=self._namespace, **kwargs)

    def addRelationship(self, left, relation, right):
        """ Create a relationship of kind 'relation' between keywords 'left'
            and 'right'.
            For example, addRelationsihp('pear', 'typeOf', 'fruit') """
        left = self.getKeyword(left)
        right = self.getKeyword(right)
        relation = self.getRelation(relation)
        newkwr = KeywordRelationship.new(left=left, relation=relation, right=right)
        newkwr.assert_valid()
        return newkwa

    def delRelationship(self, left, relation, right):
        """ Destroy the relationship of kind 'relation' between keywords 
            'left' and 'right'. """
        left = self.getKeyword(left)
        right = self.getKeyword(right)
        relation = self.getRelation(relation)
        kwr = KeywordRelationship.fetch_by(left=left,
                                           relation=relation,
                                           right=right)
        kwr.remove()

    def addAssociation(self, keyword, path):
        """ Create an association between 'keyword' and 'path'. """
        keyword = self.getKeyword(keyword)
        newkwa = KeywordAssociation.new(keyword=keyword, path=path)
        newkwa.assert_valid()
        return newkwa

    def getAssociations(self, keyword=None, path=None):
        """ Get an iterable of  associations for either the specified 'keyword'
            or the specified 'path'.  It is not an error to supply both.  It
            just doesn't make a lot of sense. """
        query = {}
        if keyword is not None:
            query['keyword'] = self.getKeyword(keyword)
        if path is not None:
            query['path'] = path

        if not query:
            raise PyolsProgrammerError("Neither a keyword or a path was given "
                                       "to getAssociations")

        return KeywordAssociation.query_by(**query)

    def delAssociations(self, keyword, path):
        """ Remove the association between keyword and path. """
        keyword = self.getKeyword(keyword)
        kwa = KeywordAssociation.fetch_by(keyword=keyword, path=path)
        kwa.remove()

    def search(self, kwName, links="all"):
        """ Search Content for a given keyword with name 'kwName'.
            By default follow all link types.  """

        keywords = self.getRelatedKeywords(kwName, links=links,
                                           cutoff = self.getSearchCutoff())

        results = []

        for kw in keywords.keys():
            obj = self.getKeyword(kw)
            rels = obj.getBRefs(self.getClassifyRelationship()) or []

            res = [(keywords[kw], x) for x in rels if self.isAllowed(x)]
            results.extend(res)

        results =  _unifyRawResults(results)

        results.sort()
        results.reverse() #descending scores
        return results

    def searchFor(self, obj, links="all"):
        """ Search for content related to obj. """

        # search not possible for non AT types
        if not getattr(obj, 'isReferenceable', 0): return []

        keywords = obj.getRefs(self.getClassifyRelationship()) or []

        results = []

        for kw in keywords:
            if kw is not None:
                results.extend(self.search(kw.getName(), links=links))

        results =  _unifyRawResults(results)

        # remove object
        results = [x for x in results if x[1]!=obj]
        results.sort()
        results.reverse()

        return results

    def getRelatedKeywords(self, keyword, fac=1, result={},
                           links="all", cutoff=0.1):
        """ Return list of keywords, that are related to 'keyword'.
            getRelatedKeywords('dog', 0.5, {'cat': 1}, "all", 0.2) =>
                {'dog': 0.5', 'cat': 1, 'golden retriever': 0.25} """

        try:
            kwObj = self.getKeyword(keyword)
        except NotFound: # nonexistant keyword
            return {}

        # work with private copy w/t reference linking
        result = result.copy()

        # if necessary initialize keyword in result list
        if not result.has_key(kwObj.getName()):
            result[kwObj.getName()] = fac

        # proper link types initialization
        if type(links) == StringType:
            if links == "all":
                # Query for all the possible relationships
                rl = getToolByName(self, 'relations_library')
                links = self.relations(rl)
            else:
                # Only use the relationship from links
                links = [links]
        # Otherwise links is a list of relationship types

        children = self._getDirectLinkTargets(kwObj, fac, links, cutoff)
        result = self._getRecursiveContent(kwObj, children, result, links, cutoff)

        return result

    def _getDirectLinkTargets(self, kwObj, fac, links, cutoff):
        """ kwObj: The keyword we're dealing with
            fac: It's relevence factor
            links: Relationships to follow
            cutoff: Stop searching below this relevence  """


        children=[]

        for rel in links:
            # The relevence of keywords related by this relationship
            # will be the relevence of this keyword * weight of the relationship
            relfac = self.getWeight(rel) * fac
            if relfac <= cutoff: continue
            children.extend([(relfac, x)
                              for x in (kwObj.getReferences(rel) or [])
                              if x is not None])

        # At this point, children will be a list of (relevence, Keyword) tuples,
        # where each Keyword relates back to the kwObj
        return _unifyRawResults(children)

    def _getRecursiveContent(self, kwObj, children, result, links, cutoff):
        """ kwObj: The keyword we're dealing with
            children: A list of (score, Keyword) tuples. See _unifyRawResults.
            result: A dictionary of {kwname: relevence} which the result will
                    be stored in.
            links: A list of relationship names to follow
            cutoff: The search cutoff.  See getRelatedKeywords. """

        for (score, kw) in children:
            cname = kw.getName()
            if result.has_key(cname): continue

            result[cname] = score

            recursive = self.getRelatedKeywords(cname, score,
                                                result, links, cutoff)

            if recursive.has_key(kwObj.getName()): #suppress direct backlinks
                del recursive[kwObj.getName()]

            for kw in recursive.keys():
                if not result.has_key(kw):
                    result[kw] = recursive[kw]

        return result

    def setSearchCutoff(self, cutoff):
        if type(cutoff) != FloatType: cutoff = float(cutoff)
        if cutoff < 0: cutoff = 0

        self._cutoff = cutoff

    def getSearchCutoff(self):
        return self._cutoff

    def searchMatchingKeywordsFor(self, obj, search, exclude=[], search_kw_proposals='false', search_linked_keywords='true'):
        """Return keywords matching a search string.
        """
        #XXX obj in method signature is obsolete
        storage = self.getStorage()
        catalog = getToolByName(self, 'portal_catalog')

        kws = dict(storage.objectItems('Keyword'))

        for item in storage.objectValues('Keyword'):
            if item.title:
                kws.update({item.title: item})

        result = difflib.get_close_matches(search.decode(self.getEncoding()), kws.keys(), n=5, cutoff=0.5)
        result = [kws[x] for x in result]

        extresult=[]
        if search_linked_keywords == 'true':
            [extresult.extend(x.getLinkedKeywords()) for x in result]


        if search_kw_proposals=='true':
            kwps = catalog.searchResults(portal_type='KeywordProposal')
            kwpsdict={}
            for el in kwps:
                if el.getObject().getParentNode().getId() != 'accepted_kws':
                    kwpsdict.update({el.getObject().getId():el.getObject()})
            result2 = difflib.get_close_matches(search, kwpsdict.keys(), n=5, cutoff=0.5)
            result2 = [kwpsdict[x] for x in result2]
            for el in result:
                for el2 in result2:
                    if el2.getId()==el.getId() or el2.title_or_id() == el.title_or_id():
                        result2.remove(el2)
            result.extend(result2)
            result.extend(extresult)

        #remove duplicates & excludes

        if type(exclude) != ListType:
            exclude = [exclude]

        set = []
        [set.append(i) for i in result if (not i in set) and (i not in exclude)]

        if len(set) > 20:
            set = set[0:20]
        return set

    def useGraphViz(self):
        return self._use_gv_tool

    def generateGraphvizMap(self):
        """Generate graph source code for GraphViz.
        """
        storage = self.getStorage()
        catalog = getToolByName(self, 'portal_catalog')

        kws=[kw_res.getObject() for kw_res in catalog.searchResults(portal_type='Keyword')]

        dot = KeywordGraph(self.getGVFont(), self.getRelFont(), self.getFocusNodeShape(), self.getFocusNodeColor(), self.getFocusNodeFontColor(), self.getFocusNodeFontSize(), self.getFirstNodeShape(), self.getFirstNodeColor(), self.getFirstNodeFontColor(), self.getFirstNodeFontSize(), self.getSecondNodeShape(), self.getSecondNodeColor(), self.getSecondNodeFontColor(), self.getSecondNodeFontSize(), self.getEdgeShape(), self.getEdgeColor(), self.getEdgeFontColor(), self.getEdgeFontSize())
        
        dot.graphHeader(kws[0])

        for node in kws:
            dot.firstLevelNode(node)
            rels = node.getRelations() 
            for rel in rels:
                  obs = node.getReferences(rel)
                  try:
                    obs.remove(self)
                  except ValueError: # self not in list
                    pass
                  for cnode in obs:
                    dot.relation(node, cnode, rel)

        dot.graphFooter()

        return dot.getValue()

    ###
    # ug... Getters and setters
    ###

    def getGVNodeShapesList(self):
        """Return the gv node shape list.
        """
        return self._nodeshapes

    def getGVEdgeShapesList(self):
        """Return the gv edge shape list.
        """
        return self._edgeshapes
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
