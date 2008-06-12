from keywordgraph import KeywordGraph

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.PortalFolder import ContentFilter
from Products.Archetypes.config import TOOL_NAME as AT_TOOL
from Products.Archetypes.atapi import *

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl import Permissions

from config import PROJECTNAME
from utils import _normalize

from types import StringType
import zLOG, string

_marker = []

kwSchema = BaseSchema + Schema((
    TextField('kwDescription'),
    StringField('short_additional_description',
                widget=StringWidget(maxlength=25,
                                    label='short additional description',
                                    ),
                ),
    ImageField("kwMapGraphic"),
    TextField("kwMapData",
              default_content_type="text/html",
              default_output_type="text/html",
              ),

    ))

class Keyword(BaseContent):
    
    meta_type = portal_type = archetype = "Keyword"
    
    global_allow = 0
    content_icon = "workflow_icon.gif"
    
    schema = kwSchema
    actions = (
        {'name' : "Related Content",
         'id' : "relatedContent",
         'action' : "string: ${object_url}/keyword_contents",
         'category' : "object_tabs",
         },
        {'name' : "View",
         'id' : "view",
         'action' : "string: ${object_url}/keyword_context_view",
         'category' : "object_tabs",
         },

        )
    
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    security.declarePublic('generateId')
    def generateId(self, id, small_des):
        """makes id string for keyword generation in workflow"""
        new_small_des = _normalize(small_des)
        if small_des!='':
            return id + '_' + new_small_des
        else:
            return id                

    security.declarePublic('title_or_id')
    def title_or_id(self):
        '''makes title string with small description'''
        t=''
        des=''
        try:
            t=self.title
        except:
            t=self.getSaneId()
        try:
            if self.short_additional_description != '':
             des=' (' + self.short_additional_description + ')'
        except:
            des=''
        return t + des

    security.declarePublic("getLinkedKeywords")
    def getLinkedKeywords(self, type=None):
        res = self.getRefs(type)
        res = [x for x in res if x is not None]
        return res

    def getWrappedKeywords(self):
        """
        returns all linked keywords wrapped together with a list of
        the corresponding relationtypes
        """
        reltypes=self.getRelationships()

        result = []
        objects = []
        
        for r in reltypes:
            obs = self.getRefs(r)
            for o in obs:
                if not o in objects:
                    objects.append(o)
                    result.append((o, [r]))
                else: #just append relationship
                    try:
                        idx = objects.find(o)
                        entry = result[idx]
                        entry[1].append(r)
                    except:
                        pass

        return result

    def _filteredItems( self, obs, filt ):
        """
            Apply filter, a mapping, to child objects indicated by 'ids',
            returning a sequence of ( id, obj ) tuples.

            From CMF1.6 PortalFolder API
        """
        # Restrict allowed content types
        if filt is None:
            filt = {}
        else:
            # We'll modify it, work on a copy.
            filt = filt.copy()
        pt = filt.get('portal_type', [])
        if type(pt) is type(''):
            pt = [pt]
        types_tool = getToolByName(self, 'portal_types')
        allowed_types = types_tool.listContentTypes()
        if not pt:
            pt = allowed_types
        else:
            pt = [t for t in pt if t in allowed_types]
        if not pt:
            # After filtering, no types remain, so nothing should be
            # returned.
            return []
        filt['portal_type'] = pt

        query = ContentFilter(**filt)
        result = []
        append = result.append
        for obj in obs:
            if query(obj):
                append( (obj.getId(), obj) )
        return result
    
    security.declarePublic("classifiedContentItems")
    def classifiedContentItems( self, filter=None ):
        """
        From Portalfolder
        Provide a filtered view onto 'objectValues', allowing only
        PortalFolders and PortalContent-derivatives to show through.

        From CMF Portalfolder (follows CMF 1.6 API)
        """
        obs = self.getBRefs('classifiedAs')
        return self._filteredItems(obs, filter)

    security.declarePublic("classifiedContentValues")
    def classifiedContentValues( self, filter=None ):
        """Return content classified for keyword.
        
        Provide a filtered view onto 'objectValues', allowing only
        PortalFolders and PortalContent-derivatives to show through.
        """
        return [x[1] for x in self.classifiedContentItems(filter)]

    security.declarePublic("classifiedContentIds")
    def classifiedContentIds( self, filter=None ):
        """
        From Portalfolder
        Provide a filtered view onto 'objectValues', allowing only
        PortalFolders and PortalContent-derivatives to show through.
        """
        return [x[0] for x in self.classifiedContentItems(filter)]

    def _recursiveFindDependent(self, levels, exact=False):
        ctool = getToolByName(self, 'portal_classification')
        forth = ctool.getForth()
        back = ctool.getBack()
        direct = []
        directback = []
        if levels == 0:
            return [self]

        if exact:
            result = []
        else:
            result = [self]
            
        if forth == '1':
         direct = self.getRefs()
         for kw in direct:
            result.extend(kw.findDependent(levels-1, exact))

        if back == '1':
         directback = self.getBRefs()
         for kw in directback:
            result.extend(kw.findDependent(levels-1, exact))

        if exact and levels>1:
            result = [x for x in result if not x==self]
            result = [x for x in result if not x in direct]
            result = [x for x in result if not x in directback]
                
        return result
    
    def findDependent(self, levels=2, exact=False):
        """
        Find keywords with shortest path distance less than level steps
        """
        temp = self._recursiveFindDependent(levels, exact)
        result = []
        for x in temp:
            if not x in result:
                result.append(x)

        return result

    def getSaneId(self):
        result = self.getId()
        result = result.replace('.', '')
        result = result.replace('_', '')
        result = result.replace('-', '')
        return result
    
    def generateGraph(self, levels=2):
        """
        Generate graph source code for GraphViz.
        """
        ctool = getToolByName(self, 'portal_classification')
        forth = ctool.getForth()
        back = ctool.getBack()
        storage = ctool.getStorage()

        innernodes = self.findDependent(1, exact=True) # level 1 keywords
        outernodes = self.findDependent(2, exact=True) # level 2 keywords

        dot = KeywordGraph(ctool.getGVFont())
        dot.graphHeader(self)

        ### Graph nodes
        dot.focusNode(self)

        for node in innernodes:
            dot.firstLevelNode(node)

        for node in outernodes:
            dot.secondLevelNode(node)

        ### relationships

        # from central node
        if forth == '1':
         for rel in self.getRelationships():
            obs = self.getRefs(rel)
            for cnode in obs:
                dot.relation(self, cnode, rel)
        if back == '1':
         for backrel in self.getBRelationships():
            obsback = self.getBRefs(backrel)
            for cnode in obsback:
                dot.relation(cnode, self, backrel)


        # from innernodes w/o back to central
        if forth == '1':
         for node in innernodes:
            rels = node.getRelationships() 
            for rel in rels:
                obs = node.getRefs(rel)
                try:
                    obs.remove(self)
                except ValueError: # self not in list
                    pass
                
                for cnode in obs:
                    dot.relation(node, cnode, rel)

        if back == '1':
         for node in innernodes:
            relsback = node.getBRelationships() 
            for backrel in relsback:
                obsback = node.getBRefs(backrel)
                try:
                    obsback.remove(self)
                except ValueError: # self not in list
                    pass
                
                for cnode in obsback:
                    dot.relation(cnode, node, backrel)

        dot.graphFooter()

        return dot.getValue()

    def updateKwMap(self, levels=2):
        """
        update kwMap cached images
        """
        ctool = getToolByName(self, 'portal_classification')
        gvtool = getToolByName(self, 'graphviz_tool')
        g = self.generateGraph(levels=levels)

        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "Updating graph for %s" % self.getId())

        result = gvtool.renderGraph(g, options=["-Tpng",])
        self.setKwMapGraphic(result, mimetype="image/png")
        
        result = gvtool.renderGraph(g, options=["-Tcmap",])
        self.setKwMapData(result, mimetype="text/html")
        
## def modify_fti(fti):
##     fti['allow_discussion'] = 1
##     # hide unnecessary tabs (usability enhancement)
##     for a in fti['actions']:
##         if a['id'] in ('references','metadata'):
##             a['visible'] = 0
##     return fti

registerType(Keyword)
