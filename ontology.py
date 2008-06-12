from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from AccessControl.SecurityInfo import ClassSecurityInfo
from Globals import InitializeClass
from Products.Archetypes.atapi import *
from cStringIO import StringIO
from xml.sax.saxutils import escape, unescape
import re

import zExceptions, zLOG
try:
    import transaction
except ImportError:
    # for Zope 2.7
    from Products.CMFCore.utils import transaction

from Products.Relations.exception import ValidationException

from owl import OWLExporter, OWLImporter

myschema = Schema((LinesField('RootKWs',
                              vocabulary='idsOfTopLevel',
                              description='Top level keywords for the ontology view',
                              multivalued=1,
                              widget=LinesWidget(),
                              ),
                  ))


class Ontology(BaseBTreeFolder):

    schema=BaseBTreeFolderSchema +myschema

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    global_allow = 0
    filter_content_types = 1
    allowed_content_types = ('Keyword',)

    def getTopLevel(self):
        """try to guess the most 'rootlike' Kewords by looking which KWs are only parents and parent to more than one KW.
        """
        listOfObjects=[]

        number=0
        for el in getToolByName(self, 'portal_classification').getStorage().contentValues():
            if u'parentOf' in el.getRelationships() and u'childOf' not in el.getRelationships():
                for il in el.getRelationships():
                    if il == u'parentOf':
                        number=number+1
                if number > 0:
                    listOfObjects.append(el)

        return listOfObjects

    def idsOfTopLevel(self):
        """
        """
        idList=[]
        for el in self.getTopLevel():
            idList.append(el.getName())
##             for il in self.RootKW:
##                 idList.append(il)

        return idList


    def objectOfIds(self):
        """
        """
        kwstorage = getToolByName(self, 'portal_classification').getStorage()
        objList=[]
        for el in self.RootKWs:
            objList.append(getattr(kwstorage, el))
        if objList==[]:
            objList=self.getTopLevel()
        if objList==[]:
            objList=getToolByName(self, 'portal_classification').getStorage().contentValues()
        return objList

    def exportVocabulary(self):
        """XML Serialization.

        In the future this might be RDF or OWL.
        2005-04-12 OWL export with exportOWL().
        """
        ct = getToolByName(self, 'portal_classification')

        file = StringIO()

        #xml header
        file.write('<?xml version="1.0"?>\n')
        file.write('<vocabulary>\n')

        #first write relation types & scores
        kwrels = ct.keywordRelations()
        if kwrels:
            file.write('  <relations>\n')
            for rel in kwrels:
                fac = ct.getRelevanceFactor(rel)
                file.write('    <relation name="%s" score="%s"/>\n' % (rel, fac))
            file.write('  </relations>\n\n')

        #write all the keywords
        keywords = self.objectValues('Keyword')
        if keywords:
            file.write('  <keywords>\n')
            for kw in keywords:
                file.write('    <keyword id="%s" title="%s">\n' % (kw.getName(), kw.title))
                if kw.getKwDescription():
                    file.write('      <description>\n')
                    file.write(kw.getKwDescription())
                    file.write('      </description>\n')

                for rel in kw.getRelationships():
                    for ref in kw.getRefs(rel):
                        file.write('      <reference dst="%s" type="%s"/>\n' % (ref.getName(), rel))

                file.write('    </keyword>\n\n')
            file.write('  </keywords>\n\n')
        file.write('</vocabulary>\n')

        return file.getvalue()

    def importVocabulary(self, file):
        """Import ontology from XML file data.

        2005-04-19 OWL import with importOWL().
        """
        dom = parse(file)

        rels = dom.getElementsByTagName("relation")
        for rel in rels: self.handleRelation(rel)

        kws = dom.getElementsByTagName("keyword")
        for kw in kws: self.handleKeyword(kw)

        for el in getToolByName(self, 'portal_classification').getStorage().contentValues():
            el.updateKwMap()
        dom.unlink() # cleanup

    def handleRelation(self, rel):
        name = rel.getAttribute('name')
        score = rel.getAttribute('score')

        ct = getToolByName(self, 'portal_classification')
        if not name in ct.keywordRelations():
            ct.registerKeywordRelation(name, factor=score)
            zLOG.LOG(PROJECTNAME, zLOG.INFO,
                     "Added relation %s with score %s" % (name, score))

    def handleKeyword(self, kw):
        """utility function for import, handles a keyword.
        """
        id = kw.getAttribute('id')
        title = kw.getAttribute('title')
        description = kw.getElementsByTagName('description')
        refs = kw.getElementsByTagName('reference')

        if not hasattr(self.aq_base, id): # create new keyword
            self.invokeFactory('Keyword', id)

        kw = getattr(self, id)

        if title:
            kw.title = title

        if description: description = description.nodeValue
        if description:
            kw.setKwDescription(description)

        for ref in refs:
            self.handleReference(kw, ref)

        pt = getToolByName(self, 'portal_catalog')
        pt.indexObject(kw)
        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "added %s" % id)
        #XXX partial commit???

    def handleReference(self, kw, ref):
        """utility function for import, handles a reference.
        """
        dst = ref.getAttribute('dst')
        if not hasattr(self.aq_base, dst): # create new keyword
            self.invokeFactory('Keyword', dst)

        dst = getattr(self, dst)

        type = ref.getAttribute('type')

        kw.addReference(dst, type)

    ### OWL type strings. External for unit tests.
    owl_types = {'transitive'        : 'TransitiveProperty',
                 'symmetric'         : 'SymmetricProperty' ,
                 'functional'        : 'FunctionalProperty',
                 'inversefunctional' : 'InverseFunctionalProperty'}

    def exportOWL(self):
        """Export keyword structure to OWL.
        """
        exporter = OWLExporter()
        entities = exporter.getEntities()

        ct = getToolByName(self, 'portal_classification')
        rl = getToolByName(self, 'relations_library')

        # Export OWL object properties.
        for prop in ct.relations(rl):
            exporter.generateObjectProperty(name               = prop,
                                            types              = [entities['owl'] + self.owl_types[t] for t in ct.getTypes(prop)],
                                            inverses           = ct.getInverses(prop),
                                            domains            = [entities['owl'] + 'Class'],
                                            ranges             = [entities['owl'] + 'Class'],
                                            labels             = [],
                                            comments           = [],
                                            descriptions       = [],
                                            propertyproperties = [('nip:weight', str(ct.getWeight(prop)))]
            )

        # Export OWL classes.
        for kw in ct.keywords():
            keyword = ct.getKeyword(kw)
            scs = [ c.getName() for c in keyword.getRefs('childOf')   ]
            ecs = [ c.getName() for c in keyword.getRefs('synonymOf') ]
            ops = []
            for p in keyword.getRelationships():
                if p not in [ 'childOf', 'parentOf', 'synonymOf' ]:
                    for c in keyword.getRefs(p):
                        ops.append((p,c.getName()))
            lang         = 'en'
            labels       = []
            comments     = []
            descriptions = []
            label       = keyword.title
            comment     = keyword.getShortAdditionalDescription()
            description = keyword.getKwDescription()
            if label:
                labels.append((lang, label))
            if comment:
                comments.append((lang, comment))
            if description:
                descriptions.append((lang, description))
            exporter.generateClass(name            = kw,
                                   superclasses    = scs,
                                   labels          = labels,
                                   comments        = comments,
                                   descriptions    = descriptions,
                                   classproperties = ops
            )

            for c in ecs:
                exporter.generateEquivalentClass(kw, c)

        return exporter.serialize()

    def importOWL(self, file):
        """Import keyword structure from OWL file 'file'.
        """
        #XXX use subtransactions for large imports!!!

        ### OWL import.
        importer = OWLImporter(self, file)
        owl_dom = importer.getDOM()
        importer.importProperties()
        error_string = importer.importClasses()

        #don't abort transaction if map generation fails
        transaction.commit()

        # Update keyword graph images
        ct = getToolByName(self, 'portal_classification')
        try:
            for el in ct.getStorage().contentValues():
                error_string = error_string + el.updateKwMap(levels=2)
        except zExceptions.NotFound:
                pass # ignore NotFound exception for silent operation without graphviz

        return error_string

registerType(Ontology)
