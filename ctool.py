from Products.CMFCore.utils import getToolByName, UniqueObject
from Products.CMFCore.ActionProviderBase import ActionProviderBase

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl import getSecurityManager, Unauthorized
from Acquisition import aq_base, aq_inner, aq_parent
from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass, PersistentMapping

from keyword import Keyword
from ontology import Ontology
from config import *

from Products.Relations import interfaces
from Products.Relations.processor import process
from Products.Relations.exception import ValidationException

import zExceptions, zLOG
import difflib, re

from types import *

import os.path

from warnings import warn

def _unifyRawResults(results):
    """
    unify result list and add scores for unique objects
    
    results is list of tuples (score, object)
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

#ALTERNATIVE unify with help of dict
##         kws = {}
##         for c in children:
##             if not kws.has_key(c[1].id):
##                 kws[c[1].id] = cExcept
##             else:
##                 kws[c[1].id] = (kws[c[1].id][0] + c[0], kws[c[1].id][1])

##         children = kws.values()
    
class ClassificationTool(UniqueObject,
                         SimpleItem,
                         ActionProviderBase): 
    """A tool to handle content syndication with keywords.
    """
    
    id = 'portal_classification' 
    meta_type= 'Classification Tool' 
    plone_tool = 1 

    security = ClassSecurityInfo()
    #XXX proper security declarations
    security.declareObjectPublic()
    
    def __init__(self):
        self.relevance_factors = PersistentMapping()
        self._cutoff = 0.1
        self._use_gv_tool = 0
        self._storage = 'kw_storage'

    def returnReadMe(self):
        """Return README file for display in configlet"""
        from config import GLOBALS
        cdir = os.path.dirname(GLOBALS['__file__'])
        filename = os.path.join(cdir, "README.txt")
        try:
            f=open(filename,'r').read()
            return f
        except:
            return 'README.txt not found'

    def addKeyword(self, name, title="",
                   description="",
                   short_description=""):
        """Create a keyword in the current onology"""
        if not name:
            raise ValidationException("Empty name for keyword specified")

        try:
            self.getKeyword(name)
            raise NameError, "Keyword '%s' already exists in current ontology" % name
        except KeyError:
            pass

        storage = self.getStorage()
        storage.invokeFactory('Keyword', id=name, title=title, short_additional_description=short_description, kwDescription=description)
        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "Added keyword %s." % name)

        return self.getKeyword(name)

    def getKeyword(self, name):
        """Return keyword 'name' from current ontology."""
        storage = self.getStorage()
        
        if not hasattr(storage, name):
            raise KeyError, "Keyword '%s' not found in current ontology" % name

        return getattr(storage, name)

    def delKeyword(self, name):
        """Remove keyword from ontology"""
        storage = self.getStorage()
        try:
            storage._delObject(name)
            zLOG.LOG(PROJECTNAME, zLOG.INFO,
                     "Removed keyword %s." % name)
        except KeyError:
            pass

    def keywords(self): 
        """
        Return a list of all existing keyword names.
        """
        #XXX use catalog search cause it's faster
        storage = self.getStorage()
        return [kw.getId() for kw in storage.objectValues('Keyword')]

    def addRelation(self, name, weight=0.0, types=[], inverses=[]):
        """
        Create a keyword relation 'name' in the Plone Relations library, if
        non-existant. 'weight' is set in any case if in [0,1]. For each item in
        the 'types' list from {'transitive', 'symmetric', 'functional',
        'inversefunctional'} an appropiate rule is created in the Relations
        ruleset. For each relation name in the 'inverses' list an
        InverseImplicator rule is created in the Relations ruleset. The inverse
        keyword relation is created in the Plone Relations library if
        non-existant. Rules for inferring types for the inverse relation are
        created.
        """
        relations_library = getToolByName(self, 'relations_library')

        relations_library.invokeFactory('Ruleset', name)
        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "Added relation %s." % name)
        
        ruleset = self.getRelation(name)
        ruleset.setTitle(name)

        self.setWeight  (name, weight)

        if type(types) != ListType:
            types = [types]
            
        self.setTypes   (name, types)

        if type(inverses) != ListType:
            inverses = [inverses]
            
        self.setInverses(name, inverses)
        
        return ruleset

    def getRelation(self, name):
        """Return the relation ruleset from the Plone Relations library.
        """
        
        relations_library = getToolByName(self, 'relations_library')
        if name not in self.relations(relations_library):
            raise KeyError, "Relation '%s' not found in library" % name

        return relations_library.getRuleset(name)

    def delRelation(self, name):
        """
        Remove the keyword relation 'name' from 'relations_library', if it
        exists.
        """
        relations_library = getToolByName(self, 'relations_library')
        if hasattr(relations_library, name):
            relations_library.manage_delObjects(name)
            zLOG.LOG(PROJECTNAME, zLOG.INFO,
                     "Removed relation %s." % name)
        
    def relations(self, relations_library):
        """
        Return a list of all existing keyword relation names in 'relations_library'.
        """
        return [r.getId() for r in relations_library.getRulesets()]

    def getWeight(self, name):
        """Return the weight of keyword relation 'name'.
        """
        r = self.getRelation(name)
        try:
            return r.weight
        except AttributeError:
            return 0.0

    def setWeight(self, name, w):
        """
        Set weight of keyword relation 'name' to 'w',
        if 'w' >= 0.
        
        
        Exceptions: If there does not exist a keyword relation 'name', KeyError occurs.
        """
        r = self.getRelation(name)
        
        if w >= 0.0:
            r.weight = w
        
    def setTypes(self, name, t):
        """
        Set the list of types of keyword relation 'name' in 'relations_library'
        to 't', if 't' is non-empty list from {'transitive', 'symmetric',
        'functional', 'inversefunctional'}. Empty list deletes all types.
        Return the list of types of keyword relation 'name'.
        
        Exceptions: If there does not exist a keyword relation 'name',
                    KeyError occurs.
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
        """Get list of types for keyword relation 'name'
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
        """
        Set inverse relations of keyword relation 'name' in 'relations_library'
        to relations in 'i', if 'i' is non-empty list of relation names. Empty
        list deletes all inverses. All relations in 'i' are created, if
        non-existant. Inferring types for relations in 'i' are created from the
        types of relation 'name'.

        Exceptions: If there does not exist a keyword relation 'name',
                    a KeyError is thrown.
        """
        ruleset = self.getRelation(name)
        current = self.getInverses(name)
        new = [x for x in i if not x in current]
        obsolete = [x for x in current if not x in i]

        for o in obsolete:
            iruleset = self.getRelation(o)
            irules = iruleset.getComponents(interfaces.IRule)
            irules = [rule for rule in irules if rule.getId().startswith('inverseOf')]
            iruleset.manage_delObjects([rule.getId() for rule in irules if rule.getInverseRuleset().getId() == ruleset.getId()])
            
        ruleset.manage_delObjects([rule.getId() for rule in ruleset.getComponents(interfaces.IRule) if re.match('inverseOf', rule.getId()) and rule.getInverseRuleset().getId() in obsolete])

        for inverse in new:
            try:
                self.getRelation(inverse)
            except KeyError:
                self.addRelation(inverse)
                
        for inverse in i:
            inverse_ruleset = self.getRelation(inverse)
            
            types         = self.getTypes(name)
            inverse_types = [t for t in types if t in ['transitive', 'symmetric']]      + \
                            ['inversefunctional' for i in range('functional' in types)] + \
                            ['functional' for i in range('inversefunctional' in types)]

            self.setTypes(inverse, inverse_types)
            
            if not hasattr(ruleset, 'inverseOf_' + inverse):
                ruleset.invokeFactory('Inverse Implicator', 'inverseOf_' + inverse)
                getattr(ruleset, 'inverseOf_' + inverse).setInverseRuleset(inverse_ruleset.UID())

            if not hasattr(inverse_ruleset, 'inverseOf_' + name):
                inverse_ruleset.invokeFactory('Inverse Implicator', 'inverseOf_' + name)
                getattr(inverse_ruleset, 'inverseOf_' + name).setInverseRuleset(ruleset.UID())

    def getInverses(self, name):
        """Get inverse relations for the relation 'name'

        If 'name' is not existing a KeyError is thrown.
        """
        ruleset = self.getRelation(name)
        return [rule.getInverseRuleset().getId() for rule in ruleset.getComponents(interfaces.IRule) if re.match('inverseOf', rule.getId())]
    
    def addReference(self, src, dst, relation):
        """
        Create an Archetype reference of type 'relation' from keyword with name
        'src' to keyword with name 'dst', if non-existant. 'src' and 'dst' are
        created, if non-existant. The reference is created through Plone
        Relations library, so relation-specific rulesets are honored.

        Exceptions: If 'relation' does not exist zExceptions.NotFound occurs.
                    If the reference does not validate in the ruleset,
                    Relations.exception.ValidationException occurs.
        """
        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "%s(%s,%s)." % (relation, src, dst))

        try:
            kw_src  = self.getKeyword(src)
        except KeyError:
            kw_src  = self.addKeyword(src)

        try:
            kw_dst  = self.getKeyword(dst)
        except KeyError:
            kw_dst  = self.addKeyword(dst)

        process(self, connect=((kw_src.UID(), kw_dst.UID(), relation),))

    
    def delReference(self, src, dst, relation):
        """
        Remove the Archetype reference of type 'relation' from keyword with
        name 'src' to keyword with name 'dst', if the reference exists. 'src'
        and 'dst' are created, if non-existant. The reference is removed
        through Plone Relations library, so relation-specific rulesets are
        honored.
        
        Exceptions: If 'relation' does not exist zExceptions.NotFound occurs.
                    If the unreference does not validate in the ruleset
                    Relations.exceptions.ValidationException occurs.
        """
        try:
            kw_src = self.getKeyword(src)
            kw_dst = self.getKeyword(dst)
        except KeyError:
            return
        
        process(self, disconnect=((kw_src.UID(), kw_dst.UID(), relation),))

    # ZMI wrappers.
    def manage_addKeyword(self, name, title='', short_additional_description='', description='', REQUEST=None):
        """
        Add new keyword.
        """
        self.addKeyword(name, title, description, short_additional_description)
        
        if REQUEST is not None:
            return self.manage_main(REQUEST)
        
    def manage_addRelation(self, name, title='', factor=1, REQUEST=None):
        """
        Add new relation between keywords.
        """
        self.addRelation(name, factor)
        
        if REQUEST is not None:
            return self.manage_relations(REQUEST)
    
    def manage_delRelations(self, ids, REQUEST=None):
        """
        Delete keyword relations.
        """
        for name in ids:
            self.delRelation(name)

        if REQUEST is not None:
            return self.manage_relations(REQUEST)
            
    def manage_changeFactors(self, name, factor=1, REQUEST=None):
        """
        Change relevancy factor/weight for relation.
        """
        self.setWeight(name, factor)

        if REQUEST is not None:
            return self.manage_relations(REQUEST)

    ### End of new API.

    def setStorageId(self, name):
        """
        Set id of current storage
        """
        self._storage = name

    def getStorageId(self):return self._storage
    
    def getStorage(self):
        """
        Return current keyword storage object
        """
        urltool = getToolByName(self, 'portal_url')
        portal = urltool.getPortalObject()

        kwstorage = getattr(portal, self.getStorageId(), None)
        
        if kwstorage is None: #create
            pt=getToolByName(self, 'portal_types')
            pt.getTypeInfo('Ontology').global_allow=True
            portal.invokeFactory('Ontology',
                                 self.getStorageId(),
                                 title='Ontology')

            pt.getTypeInfo('Ontology').global_allow=False

            kwstorage = getattr(portal, self.getStorageId(), None)
            
        return kwstorage
    
    def isAllowed(self, obj):
        """
        Return true if current user is allowed to access obj. This is
        solely to swallow Unauthorized exceptions
        """
        if obj is None: return 0
        
        try:
            if getSecurityManager().validate(self, self, obj.getId(), obj):
                return 1
        except Unauthorized:
            return 0

        return 0
                        
    def search(self, kwId, links="all"):
        """
        Search Content for a given keyword.
        By default follow all link types
        """
        storage = self.getStorage()
        
        keywords = self.getRelatedKeywords(kwId, links=links,
                                           cutoff = self.getSearchCutoff())
        
        results = []
        
        for kw in keywords.keys():
            obj = getattr(storage, kw)
            rels = obj.getBRefs('classifiedAs') or []
            
            res = [(keywords[kw], x) for x in rels if self.isAllowed(x)]
            results.extend(res)

        results =  _unifyRawResults(results)
    
        results.sort()
        results.reverse() #descending scores
        return results


    def searchFor(self, obj, links="all"):
        """
        Search related content for content object
        """

        # search not possible for non AT types
        if not getattr(obj, 'isReferenceable', 0): return []
        
        keywords = obj.getRefs('classifiedAs') or []
        
        results = []

        for kw in keywords:
            if kw is not None:
                results.extend(self.search(kw.id, links=links))

        results =  _unifyRawResults(results)

        # remove object
        results = [x for x in results if x[1]!=obj]
        results.sort()
        results.reverse()

        return results
    
    def getRelatedKeywords(self, keyword, fac=1, result={}, links="all", cutoff=0.1):
        """
        Return list of keywords, that are related to the current one,
        keyword is the keyword ID
        """
        storage = self.getStorage()
        
        try:
            kwObj = getattr(storage, keyword)
        except AttributeError: # nonexistant keyword
            return {}
            
        # work with private copy w/t reference linking
        result = result.copy() 

        # if necessary initialize keyword in result list
        if not result.has_key(kwObj.id):
            result[kwObj.id] = fac

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
                             for x in (kwObj.getRefs(rel) or []) if x is not None and relfac>cutoff])

        return _unifyRawResults(children)

    def _getRecursiveContent(self, kwObj, children, result, links, cutoff):
        for c in children:
            cid = c[1].id
            if not result.has_key(cid):
                result[cid] = c[0]
                
                recursive = self.getRelatedKeywords(cid, c[0],
                                                    result, links, cutoff)

                if recursive.has_key(kwObj.id): #suppress direct backlinks
                    del recursive[kwObj.id] 

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
        """
        Return keywords matching a search string
        """
        #XXX obj in method signature is obsolete

        storage = self.getStorage()
        catalog = getToolByName(self, 'portal_catalog')
        
        kws = dict(storage.objectItems('Keyword'))
        kwps = catalog.searchResults(portal_type='KeywordProposal')
        kwpsdict={}
        for el in kwps:
            if el.getObject().getParentNode().getId() != 'accepted_kws':
             kwpsdict.update({el.getObject().getId():el.getObject()})
            
        for item in storage.objectValues('Keyword'):
            if item.title:
                kws.update({item.title: item})
        
        result = difflib.get_close_matches(search, kws.keys(), n=5, cutoff=0.5)
        result = [kws[x] for x in result]
    
        extresult=[]
        if search_linked_keywords == 'true':
         [extresult.extend(x.getLinkedKeywords()) for x in result]

        result2 = difflib.get_close_matches(search, kwpsdict.keys(), n=5, cutoff=0.5)
        result2 = [kwpsdict[x] for x in result2]

        if search_kw_proposals=='true':
            for el in result:
                for el2 in result2:
                    if el2.getId()==el.getId():
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

    def useGraphViz(self): return self._use_gv_tool
    
InitializeClass(ClassificationTool)
