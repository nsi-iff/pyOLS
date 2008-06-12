from keywordgraph import KeywordGraph
import keyword
import owl

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.PortalFolder import ContentFilter
from Products.Archetypes.config import TOOL_NAME as AT_TOOL
from Products.Archetypes.atapi import *
from Products.validation.interfaces import ivalidator

from AccessControl.SecurityInfo import ClassSecurityInfo, ModuleSecurityInfo
from AccessControl import Permissions

from config import PROJECTNAME
from utils import _normalize

from types import StringType
import zLOG, string

from zExceptions import NotFound

module_security = ModuleSecurityInfo('Products.PloneOntology.keyword')

class XMLNCNameValidator:
    __implements__ = (ivalidator,)
    def __init__(self, name):
        self.name = name
    def __call__(self, value, *args, **kwargs):
        from Products.PloneOntology.owl import isXMLNCName
        if not isXMLNCName(value):
            return ("Validation failed (%s): '%s' is not an XML NCName." % (self.name, value))
        else:
            return 1

class UniqueNameValidator:
    __implements__ = (ivalidator,)
    def __init__(self, name):
        self.name = name
    def __call__(self, value, *args, **kwargs):
        from Products.CMFCore.utils import getToolByName
        instance = kwargs.get('instance')
        #type = kwargs.get('portal_type')
        ctool = getToolByName(instance, 'portal_classification')
        used = ctool.isUsedName(value)
        if used and used != instance:
            return ("Validation failed (%s): '%s' is already used by %s." % (self.name, value, used))
        else:
            return 1

_marker = []

kwSchema = BaseSchema + Schema((
    TextField('kwDescription',
              widget=TextAreaWidget(label='Description',
                                    description='',
                                    label_msgid='Ontology_label_kw_description',
                                    i18n_domain='Ontology',
                                   ),
             ),
    StringField('shortAdditionalDescription',
                widget=StringWidget(maxlength=25,
                                    label='Short additional description',
                                    description='Used to distinguish homonymous Titles',
                                    label_msgid='Ontology_label_description',
                                    description_msgid='Ontology_help_aditional_description',
                                    i18n_domain='Ontology',
                                   ),
                ),
    StringField('name',
                required=1,
                default_method="getKwId",
                validators=(XMLNCNameValidator('isXMLNCName'), UniqueNameValidator('isUniqueName')),
                widget=StringWidget(label='Name',
                                    description='XML NCName identifier in the ontology',
                                    condition='python: object.getName() != object.getKwId()',
                                    label_msgid='Ontology_label_name',
                                    description_msgid='Ontology_help_name',
                                    i18n_domain='Ontology',
                                   ),
                ),
    ImageField("kwMapGraphic"),
    TextField("kwMapData",
              default_content_type="text/html",
              default_output_type="text/html",
              ),

    ))

module_security.declarePublic('generateName')
def generateName(title, shortDescription=""):
    """Return a keyword name generated from 'title' and 'shortDescription'.

    The generated name is an XML NCName and 'shortDescription' is used to distinguish homonymous titles.
    """
    name = title
    if shortDescription:
        name = name + '_' + shortDescription
    return owl.toXMLNCName(name)

class Keyword(BaseContent):

    meta_type = portal_type = archetype = "Keyword"

    global_allow = 0
    content_icon = "keyword.gif"

    schema = kwSchema
    actions = (
        {
            'name'     : "Related Content",
            'id'       : "relatedContent",
            'action'   : "string: ${object_url}/keyword_contents",
            'category' : "object_tabs",
        },
        {
            'name'     : "View",
            'id'       : "view",
            'action'   : "string: ${object_url}/keyword_context_view",
            'category' : "object_tabs",
        },
        {
            'name'     : "Manage Relations",
            'id'       : "manageRelations",
            'action'   : "string: ${object_url}/relations_adddelete",
            'category' : "object_tabs",
         },
    )
    aliases = {
        '(Default)' : 'keyword_context_view',
        'view'      : 'keyword_context_view'
    }

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    #security.declarePublic('generateId')
    #def generateId(self, id, small_des):
        #"""makes id string for keyword generation in workflow"""
        #new_small_des = _normalize(small_des)
        #if small_des!='':
            #return id + '_' + new_small_des
        #else:
            #return id

    def getKwId(self):
        # wrapper method needed for schema name field widget condition logic.
        return self.id

    security.declarePublic('generateName')
    def generateName(self, title, shortDescription=""):
        return keyword.generateName(title, shortDescription)

    def at_post_create_script(self):
        name = self.getName()
        if not name or name == self.getId():
            name = keyword.generateName(self.Title(), self.getShortAdditionalDescription())
        ctool = getToolByName(self, 'portal_classification')
        ctool.addKeyword(name, self.Title(), self.getKwDescription(), self.getShortAdditionalDescription(), self.getId())
        self.updateKwMap()

    def at_post_edit_script(self):
        self.reindexObject()
        self.updateKwMap()

    security.declarePublic('title_or_id')
    def title_or_id(self):
        """makes title string with small description.
        """
        t = self.Title() or self.getName()
        d = self.getShortAdditionalDescription()
        if d:
            return t + ' (' + d + ')'
        else:
            return t

    security.declarePublic("getLinkedKeywords")
    def getLinkedKeywords(self, type=None):
        res = self.getReferences(type)
        res = [x for x in res if x is not None]
        return res

    def getReferences(self, relation=None):
        ctool = getToolByName(self, 'portal_classification')
        rlib  = getToolByName(self, 'relations_library')
        if relation:
            rel_id = ctool.getRelation(relation).getId()
        else:
            rel_id = [ctool.getRelation(rel).getId() for rel in ctool.relations(rlib)]
        return self.getRefs(rel_id)

    def getBackReferences(self, relation=None):
        ctool = getToolByName(self, 'portal_classification')
        rlib  = getToolByName(self, 'relations_library')
        if relation:
            rel_id = ctool.getRelation(relation).getId()
        else:
            rel_id = [ctool.getRelation(rel).getId() for rel in ctool.relations(rlib)]
        return self.getBRefs(rel_id)

    def getRelations(self):
        ctool = getToolByName(self, 'portal_classification')
        rlib  = getToolByName(self, 'relations_library')
        return [rlib.getRuleset(rel_id).Title() for rel_id in self.getRelationships() if rel_id != ctool.getClassifyRelationship()]

    def getBackRelations(self):
        ctool = getToolByName(self, 'portal_classification')
        rlib  = getToolByName(self, 'relations_library')
        return [rlib.getRuleset(rel_id).Title() for rel_id in self.getBRelationships() if rel_id != ctool.getClassifyRelationship()]

    def getWrappedKeywords(self):
        """returns all linked keywords wrapped together with a list of the corresponding relationtypes.
        """
        reltypes=self.getRelations()

        result = []
        objects = []

        for r in reltypes:
            obs = self.getReferences(r)
            for o in obs:
                if not o in objects:
                    objects.append(o)
                    result.append((o, [r]))
                else: #just append relationship
                    try:
                        idx = objects.index(o)
                        entry = result[idx]
                        entry[1].append(r)
                    except:
                        pass

        return result

    def _filteredItems( self, obs, filt ):
        """Apply filter, a mapping, to child objects indicated by 'ids', returning a sequence of ( id, obj ) tuples.

        From CMF1.6 PortalFolder API.
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
        """Provide a filtered view onto 'objectValues', allowing only PortalFolders and PortalContent-derivatives to show through.

        From CMF Portalfolder (follows CMF 1.6 API).
        """
        ctool = getToolByName(self, 'portal_classification')
        obs = self.getBRefs(ctool.getClassifyRelationship())
        return self._filteredItems(obs, filter)

    security.declarePublic("classifiedContentValues")
    def classifiedContentValues( self, filter=None ):
        """Return content classified for keyword.

        Provide a filtered view onto 'objectValues', allowing only        PortalFolders and PortalContent-derivatives to show through.
        """
        return [x[1] for x in self.classifiedContentItems(filter)]

    security.declarePublic("classifiedContentIds")
    def classifiedContentIds( self, filter=None ):
        """Provide a filtered view onto 'objectValues', allowing only PortalFolders and PortalContent-derivatives to show through.

        From Portalfolder.
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
            direct = self.getReferences()
            for kw in direct:
                result.extend(kw.findDependent(levels-1, exact))

        if back == '1':
            directback = self.getBackReferences()
            for kw in directback:
                result.extend(kw.findDependent(levels-1, exact))

        if exact and levels>1:
            result = [x for x in result if not x==self]
            result = [x for x in result if not x in direct]
            result = [x for x in result if not x in directback]
        return result

    def findDependent(self, levels=2, exact=False):
        """Find keywords with shortest path distance less than level steps.
        """
        temp = self._recursiveFindDependent(levels, exact)
        result = []
        for x in temp:
            if not x in result:
                result.append(x)

        return result

    def generateGraph(self, levels=2):
        """Generate graph source code for GraphViz.
        """
        ctool = getToolByName(self, 'portal_classification')
        forth = ctool.getForth()
        back = ctool.getBack()

        innernodes = self.findDependent(1, exact=True) # level 1 keywords
        outernodes = self.findDependent(2, exact=True) # level 2 keywords

        dot = KeywordGraph(ctool.getGVFont(), ctool.getRelFont(), ctool.getFocusNodeShape(), ctool.getFocusNodeColor(), ctool.getFocusNodeFontColor(), ctool.getFocusNodeFontSize(), ctool.getFirstNodeShape(), ctool.getFirstNodeColor(), ctool.getFirstNodeFontColor(), ctool.getFirstNodeFontSize(), ctool.getSecondNodeShape(), ctool.getSecondNodeColor(), ctool.getSecondNodeFontColor(), ctool.getSecondNodeFontSize(), ctool.getEdgeShape(), ctool.getEdgeColor(), ctool.getEdgeFontColor(), ctool.getEdgeFontSize())
        
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
         for rel in self.getRelations():
            obs = self.getReferences(rel)
            for cnode in obs:
                dot.relation(self, cnode, rel)
        if back == '1':
         for backrel in self.getBackRelations():
            obsback = self.getBackReferences(backrel)
            for cnode in obsback:
                dot.relation(cnode, self, backrel)


        # from innernodes w/o back to central
        if forth == '1':
         for node in innernodes:
            rels = node.getRelations() 
            for rel in rels:
                obs = node.getReferences(rel)
                try:
                    obs.remove(self)
                except ValueError: # self not in list
                    pass

                for cnode in obs:
                    dot.relation(node, cnode, rel)

        if back == '1':
         for node in innernodes:
            relsback = node.getBackRelations()
            for backrel in relsback:
                obsback = node.getBackReferences(backrel)
                try:
                    obsback.remove(self)
                except ValueError: # self not in list
                    pass

                for cnode in obsback:
                    dot.relation(cnode, node, backrel)

        dot.graphFooter()

        return dot.getValue()

    def updateKwMap(self, levels=2):
        """Update kwMap cached images. Returns string containing error messages, empty if none.
        """
        ctool = getToolByName(self, 'portal_classification')
        gvtool = getToolByName(self, 'graphviz_tool')

        if not gvtool.isLayouterPresent():
            raise NotFound(gvtool.getLayouter())

        g = self.generateGraph(levels=levels)

        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "Updating graph for '%s' with layouter %s." % (self.getName(), gvtool.getLayouter()))

        (result, error) = gvtool.renderGraph(g, options=["-Tpng",])
        self.setKwMapGraphic(result, mimetype="image/png")

        (result, error) = gvtool.renderGraph(g, options=["-Tcmap",])
        self.setKwMapData(result, mimetype="text/html")

        return error

## def modify_fti(fti):
##     fti['allow_discussion'] = 1
##     # hide unnecessary tabs (usability enhancement)
##     for a in fti['actions']:
##         if a['id'] in ('references','metadata'):
##             a['visible'] = 0
##     return fti

registerType(Keyword)
