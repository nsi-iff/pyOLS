from pyols.model import Keyword, Namespace
from pyols.fonts import findFonts

import difflib
from types import *

def _unifyRawResults(results):
    """unify result list and add scores for unique objects.

    results is list of tuples (score, object).
    """

    result = []
    obs = []
    for c in results:
        if not c[1] in obs:
            result.append(c)
            obs.append(c[1])
        else:
            index = obs.index(c[1])
            result[index] = (result[index][0] + c[0], result[index][1])

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

    def addKeyword(self, name, disambiguation='', description=''):
        """ Create a keyword in the ontology.
            An error will be raised if a keyword with the same name
            and disambiguation exists in the current namespace. """

        newkw = Keyword.new(namespace=self._namespace, name=name,
                            disambiguation=disambiguation,
                            description=description)
        newkw.assert_valid()

    def getKeyword(self, name):
        """ Return keyword 'name' from current ontology.
            An exception is raised if the keyword is not found. """
        return Keyword.fetch_by(name=name)        

    def delKeyword(self, name):
        """ Remove keyword 'name', along with all dependent associatons
            and relationships from the current ontology. """

        kw = self.getKeyword(name)
        kw.expunge()

    def keywords(self):
        """Return a list of all existing keyword names.
        """
        catalog = getToolByName(self, 'portal_catalog')

        return [kw_res.getObject().getName() for kw_res in catalog.searchResults(portal_type='Keyword')]

    def addRelation(self, name, weight=0.0, types=[], inverses=[], uid=""):
        """Create a keyword relation 'name' in the Plone Relations library, if non-existant.

        'weight' is set in any case if in [0,1]. For each item in the 'types' list from {'transitive', 'symmetric', 'functional', 'inversefunctional'} an appropiate rule is created in the Relations ruleset. For each relation name in the 'inverses' list an InverseImplicator rule is created in the Relations ruleset. The inverse keyword relation is created in the Plone Relations library if non-existant. Rules for inferring types for the inverse relation are created. If 'uid' is specified, the referenced relation ruleset is registered as relation 'name'.

        Exceptions:
            ValidationException : 'name' is not a valid XML NCName.
            NameError           : Relation 'name' already exists in current ontology.
            AttributeError      : 'uid' references no relation in current ontology.
        """
        if not owl.isXMLNCName(name):
            raise ValidationException("Invalid name for relation specified")

        if self.isUsedName(name, 'Ruleset'):
            raise NameError, "Relation '%s' already exists in current ontology" % name

        relations_library = getToolByName(self, 'relations_library')

        if not uid:
            uid = generateUniqueId('Ruleset')
            relations_library.invokeFactory('Ruleset', uid)

        ruleset = relations_library.getRuleset(uid)
        ruleset.setTitle(name)
        ruleset.reindexObject()
        ruleset.unmarkCreationFlag()

        self.setWeight  (name, weight)

        if type(types) != ListType:
            types = [types]
        self.setTypes   (name, types)

        if type(inverses) != ListType:
            inverses = [inverses]
        self.setInverses(name, inverses)

        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "Added relation %s." % name)

        return ruleset

    def getRelation(self, name):
        """Return ruleset for keyword relation 'name' of current ontology from the Plone Relations library.

        Exceptions:
            NotFound            : There is no relation 'name' in current ontology.
            ValidationException : 'name' is empty.
        """
        catalog = getToolByName(self, 'portal_catalog')

        if not name:
            raise ValidationException, "Empty relation name."

        try:
            return catalog.searchResults(portal_type='Ruleset', Title=name)[0].getObject()
        except IndexError:
            raise NotFound, "Relation '%s' not found in current ontology" % name

    def delRelation(self, name):
        """Remove the keyword relation 'name' from current ontology, if it exists.
        """
        relations_library = getToolByName(self, 'relations_library')
        try:
            relations_library.manage_delObjects(self.getRelation(name).getId())
            zLOG.LOG(PROJECTNAME, zLOG.INFO, "Removed relation %s." % name)
        except:
            pass

    def relations(self, relations_library, plus='0'):
        """Return a list of all existing keyword relation names in 'relations_library' and add ['noChange', 'deleteAll'] if plus != '0'
        """
        rel_list=['noChange', 'deleteAll']
        if plus != '0':
         for r in relations_library.getRulesets():
          rel_list.append(r.Title()) 
         return rel_list
        else:
         return [r.Title() for r in relations_library.getRulesets()]

    def getWeight(self, name):
        """Return the weight of keyword relation 'name'.

        Exceptions:
            NotFound : No relation 'name' in current ontology.
        """
        r = self.getRelation(name)
        try:
            return r.weight
        except AttributeError:
            return 0.0

    def setWeight(self, name, w):
        """Set weight of keyword relation 'name' to 'w', if 'w' >= 0.

        Exceptions:
            NotFound : No relation 'name' current ontology.
        """
        r = self.getRelation(name)

        if w >= 0.0:
            r.weight = w

    def setTypes(self, name, t):
        """Set the list of types of keyword relation 'name'.

        The list is set to t, if 't' is non-empty list from {'transitive', 'symmetric', 'functional', 'inversefunctional'}. Empty list deletes all types.
        Return the list of types of keyword relation 'name'.

        Exceptions:
            NotFound : No relation 'name' in current ontology.
        """

        r = self.getRelation(name)

        if 'transitive' in t:
            r.transitive = True
        elif hasattr(r, 'transitive'):
            delattr(r, 'transitive')

        if 'symmetric' in t:
            if not hasattr(r, 'symmetric'):
                r.invokeFactory('Inverse Implicator', 'symmetric')
                r.symmetric.setInverseRuleset(r.UID())
                r.symmetric.setTitle('Symmetric')
        else:
            try:
                r.manage_delObjects('symmetric')
            except AttributeError:
                pass
    
        if 'functional' in t:
            if not hasattr(r, 'functional'):
                r.invokeFactory('Cardinality Constraint', 'functional')
                r.functional.setMinTargetCardinality(0)
                r.functional.setMaxTargetCardinality(1)
        else:
            try:
                r.manage_delObjects('functional')
            except AttributeError:
                pass

        if 'inversefunctional' in t:
            if not hasattr(r, 'inversefunctional'):
                r.invokeFactory('Cardinality Constraint', 'inversefunctional')
                r.inversefunctional.setMinSourceCardinality(0)
                r.inversefunctional.setMaxSourceCardinality(1)
        else:
            try:
                r.manage_delObjects('inversefunctional')
            except AttributeError:
                pass

    def getTypes(self, name):
        """Get list of types for keyword relation 'name'.

        Exceptions:
            NotFound : No relation 'name' in current ontology.
        """
        ruleset = self.getRelation(name)

        result = []
        try:
            if ruleset.transitive:
                result.append('transitive')
        except AttributeError:
            pass

        result.extend([rule.getId() for rule in ruleset.getComponents(interfaces.IRule) if rule.getId() in ('symmetric', 'functional', 'inversefunctional')])

        return result
        
    def setInverses(self, name, i):
        """Set inverse relations of keyword relation 'name'.

        Inverse relations are set to relations in 'i', if 'i' is non-empty list of relation names. Empty list deletes all inverses. All relations in 'i' are created, if non-existant. Inferring types for relations in 'i' are created from the types of relation 'name'.

        Exceptions:
            NotFound : No relation ruleset 'name' in current ontology.
        """
        ruleset = self.getRelation(name)
        current = self.getInverses(name)
        new = [x for x in i if not x in current]
        obsolete = [x for x in current if not x in i]

        for o in obsolete:
            iruleset = self.getRelation(o)
            irules = iruleset.getComponents(interfaces.IRule)
            irules = [rule for rule in irules if rule.getId().startswith('inverseOf')]
            iruleset.manage_delObjects([rule.getId() for rule in irules if rule.getInverseRuleset().Title() == ruleset.Title()])

        ruleset.manage_delObjects([rule.getId() for rule in ruleset.getComponents(interfaces.IRule) if rule.getId().startswith('inverseOf_') and rule.getInverseRuleset().Title() in obsolete])

        for inverse in new:
            try:
                self.getRelation(inverse)
            except NotFound:
                self.addRelation(inverse)

        for inverse in i:
            inverse_ruleset = self.getRelation(inverse)

            types         = self.getTypes(name)
            inverse_types = [t for t in types if t in ['transitive', 'symmetric']]      + \
                            ['inversefunctional' for i in range('functional' in types)] + \
                            ['functional' for i in range('inversefunctional' in types)]

            self.setTypes(inverse, inverse_types)

            if not hasattr(ruleset, 'inverseOf_' + inverse_ruleset.getId()):
                ruleset.invokeFactory('Inverse Implicator', 'inverseOf_' + inverse_ruleset.getId())
                getattr(ruleset, 'inverseOf_' + inverse_ruleset.getId()).setTitle('inverseOf: ' + inverse)
                getattr(ruleset, 'inverseOf_' + inverse_ruleset.getId()).setInverseRuleset(inverse_ruleset.UID())

            if not hasattr(inverse_ruleset, 'inverseOf_' + ruleset.getId()):
                inverse_ruleset.invokeFactory('Inverse Implicator', 'inverseOf_' + ruleset.getId())
                getattr(inverse_ruleset, 'inverseOf_' + ruleset.getId()).setTitle('inverseOf: ' + name)
                getattr(inverse_ruleset, 'inverseOf_' + ruleset.getId()).setInverseRuleset(ruleset.UID())

    def getInverses(self, name):
        """Get inverse relations for the relation 'name'.

        Exceptions:
            NotFound : No relation ruleset 'name' in current ontology.
        """
        ruleset = self.getRelation(name)
        return [rule.getInverseRuleset().Title() for rule in ruleset.getComponents(interfaces.IRule) if rule.getId().startswith('inverseOf_')]
        
    def addReference(self, src, dst, relation, ):
        """Create an Archetype reference of type 'relation' from keyword with name
        'src' to keyword with name 'dst', if non-existant.

        'src' and 'dst' are created, if non-existant. The reference is created through Plone Relations library, so relation-specific rulesets are honored.

        Exceptions:
            NotFound            : No relation 'relation' in current ontology.
            ValidationException : Reference does not validate in the relation ruleset or 'src' or 'dst' are invalid XMLNCNames
        """
        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "%s(%s,%s)." % (relation, src, dst))

        relations_library = getToolByName(self, 'relations_library')

        try:
            kw_src  = self.getKeyword(src)
        except NotFound:
            kw_src  = self.addKeyword(src)

        try:
            kw_dst  = self.getKeyword(dst)
        except NotFound:
            kw_dst  = self.addKeyword(dst)

        process(self, connect=((kw_src.UID(), kw_dst.UID(), self.getRelation(relation).getId()),))


    def delReference(self, src, dst, relation):
        """Remove the Archetype reference of type 'relation' from keyword with
        name 'src' to keyword with name 'dst', if the reference exists.

        'src' and 'dst' are created, if non-existant. The reference is removed through Plone Relations library, so relation-specific rulesets are honored.

        Exceptions:
            NotFound            : No relation 'relation' in current ontology.
            ValidationException : Unreference does not validate in the relation ruleset.
        """
        try:
            kw_src = self.getKeyword(src)
            kw_dst = self.getKeyword(dst)
        except NotFound:
            return

        process(self, disconnect=((kw_src.UID(), kw_dst.UID(), self.getRelation(relation).getId()),))

    def search(self, kwName, links="all"):
        """Search Content for a given keyword with name 'kwName'.

        By default follow all link types.
        """

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
        """Search related content for content object.
        """

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

    def getRelatedKeywords(self, keyword, fac=1, result={}, links="all", cutoff=0.1):
        """Return list of keywords, that are related to keyword with name 'keyword'.
        """

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
                rl = getToolByName(self, 'relations_library')
                links = self.relations(rl)
            else:
                links = [links]

        children = self._getDirectLinkTargets(kwObj, fac, links, cutoff)
        result = self._getRecursiveContent(kwObj, children, result, links, cutoff)

        return result

    def _getDirectLinkTargets(self, kwObj, fac, links, cutoff):
        children=[]

        for rel in links:
            relfac = self.getWeight(rel) * fac
            children.extend([(relfac, x)
                             for x in (kwObj.getReferences(rel) or []) if x is not None and relfac>cutoff])

        return _unifyRawResults(children)

    def _getRecursiveContent(self, kwObj, children, result, links, cutoff):
        for c in children:
            cname = c[1].getName()
            if not result.has_key(cname):
                result[cname] = c[0]

                recursive = self.getRelatedKeywords(cname, c[0],
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

#def \(getGVNodeShapesList\|getGVEdgeShapesList\|getFocusNodeShape\|setFocusNodeShape\|getFocusNodeColor\|setFocusNodeColor\|getFocusNodeFontColor\|setFocusNodeFontColor\|getFocusNodeFontColor\|setFocusNodeFontColor\|getFocusNodeFontSize\|setFocusNodeFontSize\|getFocusNodeShape\|setFocusNodeColor\|getFocusNodeColor\|setFocusNodeColor\|getFocusNodeFontColor\|setFocusNodeFontColor\|getFocusNodeFontColor\|setFocusNodeFontColor\|getFocusNodeFontSize\|setFocusNodeFontSize\|getFirstNodeShape\|setFirstNodeShape\|getFirstNodeColor\|setFirstNodeColor\|getFirstNodeFontColor\|setFirstNodeFontColor\|getFirstNodeFontColor\|setFirstNodeFontColor\|getFirstNodeFontSize\|setFirstNodeFontSize\|getSecondNodeShape\|setSecondNodeShape\|getSecondNodeColor\|setSecondNodeColor\|getSecondNodeFontColor\|setSecondNodeFontColor\|getSecondNodeFontColor\|setSecondNodeFontColor\|getSecondNodeFontSize\|setSecondNodeFontSize\|getEdgeShape\|setEdgeShape\|getEdgeColor\|setEdgeColor\|getEdgeFontColor\|setEdgeFontColor\|getEdgeFontColor\|setEdgeFontColor\|getEdgeFontSize\|setEdgeFontSize\|getGVFontList\|getFontPath\|getGVFont\|setGVFont\|getRelFont\|setRelFont\|getBack\|setBack\|getForth\|setForth\|getEncoding\|setEncoding\|addKeyword\|getKeyword\|delKeyword\|keywords\|addRelation\|getRelation\|delRelation\|relations\|getWeight\|setWeight\|setTypes\|getTypes\|setInverses\|getInverses\|addReference\|delReference\|search\|searchFor\|getRelatedKeywords\|_getDirectLinkTargets\|_getRecursiveContent\|setSearchCutoff\|getSearchCutoff\|searchMatchingKeywordsFor\|useGraphViz\|generateGraphvizMap\)
