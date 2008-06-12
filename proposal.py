from Products.CMFCore.utils import getToolByName
from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import *
from Products.CMFCore import CMFCorePermissions
from Products.Archetypes.Widget import LinesWidget
from Products.Archetypes.Schema import MetadataSchema
from widget import *
from Acquisition import aq_base, aq_acquire, aq_inner, aq_parent
from config import PROJECTNAME
from utils import _normalize

import string, keyword

MyBaseSchema = BaseSchema.copy()
MyBaseSchema['title'].widget=ActiveStringWidget() 
MyBaseSchema['title'].widget.label = 'New Keyword' 
MyBaseSchema['title'].widget.description = "Can contain capital letters, spaces etc."
MyBaseSchema['title'].mutator='setTitle'
MyBaseSchema['id'].widget.visible = {'view':'invisible',
                                      'edit':'invisible'}

schema = MyBaseSchema +Schema((
    StringField('shortAdditionalDescription',
                default='',
                widget=StringWidget(maxlength=25,
                                    label='short additional description',
                                    description='in case there are two completely different meanings for a keyword, please specify e.g. Neuron (the cell) or Neuron (the simulation software)',),),

    TextField('keywordProposalDescription',
              default='',
              widget=TextAreaWidget(label="description of new keyword",
                                    description="description of new keyword",),),

    ReferenceField('RelationProposals',
                   relationship='hasRelation',
                   allowed_types=('RelationProposal',),
                   vocabulary_display_path_bound=50,
                   multiValued=True,
                   widget = MyRefWidget(label="RelationProposals",
                                        addable = True,
                                        destination_types=('RelationProposal',),
                                        destination = '.',),),
    ))

class KeywordProposal(BaseFolder):
    """Proposal for a new keyword to be added to the Ontology ttw
    """

    security = ClassSecurityInfo()
    schema = schema
    allowed_content_types = ['RelationProposal',]
    meta_type = portal_type = 'KeywordProposal'
    archetype_name = 'Keyword Proposal'

    security.declarePublic('setTitle')
    def setTitle(self, value,):
        """custom mutator to change the id and title as well"""
        id = self.getId()
        if value:
          id = self._generateId(value)
          self.setId(id)
        self.title=value

    security.declarePublic('title_or_id')
    def title_or_id(self):
        """makes title string with small description"""
        t=''
        des=''
        try:
            t=self.title
        except:
            t=self.getId()
        try:
            if self.short_additional_description != '':
             des=' (' + self.short_additional_description + ')'
        except:
            des=''
        return t + des

    security.declarePublic('generateName')
    def generateName(self, title, shortDescription=""):
        return keyword.generateName(title, shortDescription)

    def _generateId(self, value):
        """
        """
        new_id = _normalize(value)
        x=1
        if new_id in self.aq_inner.aq_parent.objectIds():
            if getattr(self, new_id).UID() != self.UID():
              id_list = new_id.split('_')
              new_id = id_list[0] + '_' + str(x)
              x=x+1
        return new_id

    def getPKWDescription(self):
        """
        """
        if self.keywordProposalDescription:
            return self.keywordProposalDescription
        else:
            return ''

    security.declarePublic('getKPId')
    def getKPId(self):
        """
        """
        return self.getId()

    security.declarePublic('getWfThing')
    def getWfThing(self,):
        """
        """
        return getToolByName(self, 'portal_workflow', None).getStatusOf('relation_proposal_workflow',self)

    security.declarePublic('getKPTitle')
    def getKPTitle(self):
        """
        """
        return self.title

    security.declarePublic('makeTitlefromKw')
    def makeTitlefromKw(self):
        """make compatible keyword title
        """
        return string.replace(string.capitalize(string.lower(self.getKeywordProposal())),'_',' ',)

    security.declarePublic('definedRelations')
    def definedRelations(self):
        """get existing relations
        """
        ct=getToolByName(self, 'portal_classification', None)
        hello=[]
        for el in ct.keywordRelations():
            hello.append(el)
        hello.append('DiscardThisRelation')
        return hello

    def Relations(self):
        """accessor: a list of strings
        """
        exrel=self.getRelationsList()
        together=''
        for el in exrel:
            if el['relationType'] and el['existingKeyword']:
                together=together + 'is ' + '<b>'  + el['relationType'] + '</b> ' + el['existingKeyword'] + '<br />'
        return together

    def getRelationsList(self):
        """edit_accessor

        a list of dictionaries suitable for the edit form
        """
        helli=[]
        if hasattr(self, 'relations'):
            for el in self.relations:
                hello={'relationType':'', 'existingKeyword':''}
                hello['relationType']=el.get('relationType', '')
                hello['existingKeyword']=el.get('existingKeyword', '')
                helli.append(hello)
            return helli
        else:
            return []

    def getNextRT(self, nextrelation={}):
        """
        """
        return nextrelation.get('relationsType','')

    def getNextEK(self, nextrelation={}):
        """
        """
        return nextrelation.get('existingKeyword','')

    def setRelations(self, relations=[], nextrelation={}):
        """mutator

        handles records/record construct from the edit form
        """
        for el in relations:
            if el['relationType']=='DiscardThisRelation':
                relations.remove(el)
            elif el['relationType']!='DiscardThisRelation' and el.get('existingKeyword','')=='':
                relations.remove(el)

        self.relations=relations

        if nextrelation and nextrelation[0].get('existingKeyword','')!='' and not nextrelation[0]['relationType']=='DiscardThisRelation':
            counter=0
            for el in relations:
                if el['relationType'] == nextrelation[0]['relationType'] and el['existingKeyword'] == nextrelation[0]['existingKeyword']:
                    counter=counter+1
            if counter == 0:
                self.relations.append(nextrelation[0])

    def pre_validate(self, REQUEST, errors):
        """
        """
        if REQUEST.get('more_relations',None):
            self.setRelations(REQUEST.get('relations',[]),
                            REQUEST.get('nextrelation',None))
            if REQUEST.form.get('nextrelation',None):
                del REQUEST.form['nextrelation']
            errors['relations']='Next relation enabled'
        elif REQUEST.get('form_submit',None):
            self.setRelations(REQUEST.get('relations',[]),
                              REQUEST.get('nextrelation',None))
            if REQUEST.form.get('nextrelation',None):
                del REQUEST.form['nextrelation']

registerType(KeywordProposal, PROJECTNAME)

MyBaseSchema = BaseSchema.copy()
MyBaseSchema['id'].widget.visible = {'view':'invisible',
                                      'edit':'invisible'}
MyBaseSchema['title'].required = 0
MyBaseSchema['title'].widget.visible = {'view':'invisible',
                                         'edit':'invisible'}
schema = MyBaseSchema +Schema((
    StringField('SearchKWA',
                default='',
                searchable=0,
                required=1,
                widget=SearchKWAWidget(label='KeywordA',
                                       condition='python:object.showKWA()',),
                enforceVocabulary=0,
                ),
    StringField('relation',
               searchable=1,
               required=1,
               multivalued=0,
               widget=SelectionWidget(label='Relation',
                                  description="How keyword a is related to keyword b",
               ),
               vocabulary="definedRelations",
               ),
    StringField('SearchKWB',
                default='',
                searchable=0,
                mutator='setSearchKWB',
                required=1,
                widget=SearchKWBWidget(label='KeywordB',),
                enforceVocabulary=0,
                ),
    ))

class RelationProposal(BaseContent):
    """Proposal for new relation between keywords

    This class together with an accompanying workflow controls
    the way new links between keywords are created.
    """
    security = ClassSecurityInfo()
    schema = schema
    meta_type = portal_type = 'RelationProposal'
    archetype_name = 'Relation Proposal'

    def pre_validate(self, REQUEST, errors):
        """
        """
        if self.getParentNode().meta_type == 'KeywordProposal' and REQUEST.get('SearchKWA',None) == None:
         REQUEST.form['SearchKWA'] = 'Keyword Proposal'

    security.declarePublic('generateKwId')
    def generateKwId(self, id, small_des):
        '''makes id string for keyword generation in workflow'''
        new_small_des = _normalize(small_des)
        if small_des!='':
            return id + '_' + new_small_des
        else:
            return id

    security.declarePublic('getSearchKWA')
    def getSearchKWA(self):
        '''get value of SearchKWA or get the parent KeywordProposal'''
        if self.getParentNode().meta_type != 'KeywordProposal':
         return self.SearchKWA
        else:
         return self.getParentNode().title

    security.declarePublic('setSearchKWB')
    def setSearchKWB(self, value):
        '''set value of SearchKWB + make a title out of it'''
        if self.getParentNode().meta_type != 'KeywordProposal':
         self.SearchKWB=value
        else:
         self.SearchKWB=value
        self.title=self.title_or_id()

    security.declarePublic('title_or_id')
    def title_or_id(self):
        '''makes title string out of the relation'''
        ct=getToolByName(self, 'portal_classification', None)
        try:
            a=self.getSearchKWA()
            if self.getSearchKWA() == 'Keyword Proposal':
             a=''
        except:
            a=''
        return a+' '+self.getRelation()+' '+self.getSearchKWB()

    security.declarePublic('getPKWDescription')
    def getPKWDescription(self):
        '''d'''
        if self.keywordProposalDescription:
            return self.keywordProposalDescription
        else:
            return ''

    def getNameOfReferencedKeyword(self, url=''):
        liste=[]
        at=getToolByName(self, 'archetype_tool', None)
        liste=url.split('/')
        objId=liste[len(liste)-1]
        return getattr(self, objId).title_or_id()

    def getURLOfUID(self, uid=''):
        at=getToolByName(self, 'archetype_tool', None)
        return at.lookupObject(uid).absolute_url()

    def getTitleOrIdOfReferencedKeyword(self, url=''):
        liste=[]
        at=getToolByName(self, 'archetype_tool', None)
        liste=url.split('/')
        objId=liste[len(liste)-1]
        return getattr(self, objId).title_or_id()

    security.declarePublic('getTitleOrIdOfUID')
    def getTitleOrIdOfUID(self, kw=''):
        at=getToolByName(self, 'archetype_tool', None)
        this=at.lookupObject(kw)
        return this.title_or_id()

    security.declarePublic('showKWA')
    def showKWA(self):
        '''shows SearchKWA Field unless we have a Relation within a KWProposal'''
        if self.getParentNode().meta_type != 'KeywordProposal':
         return 1
        else:
         return 0

    security.declarePublic('definedRelations')
    def definedRelations(self):
        '''get existing relations'''
        ct=getToolByName(self, 'portal_classification', None)
        return ct.relations(relations_library=getToolByName(self, 'relations_library'))

registerType(RelationProposal, PROJECTNAME)
