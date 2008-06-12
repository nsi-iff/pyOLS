from Products.Archetypes.atapi import *
from Products.Archetypes.Schema import MetadataSchema
from Products.Archetypes.Widget import TypesWidget, ReferenceWidget
from widget import ActiveStringWidget, ClassificationWidget, SearchKWWidget

ClassificationSchema = Schema((
    StringField('SearchKW',
                default='',
                searchable=0,
                required=0,
                schemata="classification",
                widget=SearchKWWidget(label='Keyword',
                                      description='classify your content here. if your browser has javascript enabled a drop down box should appear while you type',
                                          visible = {'view':'invisible',
                                          'edit':'visible'}),
                enforceVocabulary=0,
                ),

    ReferenceField('categories',
                   multiValued=1,
                   allowed_types=('Keyword',),
                   relationship='classifiedAs',
                   destination='/kw_storage',
                   schemata="classification",
                   widget=ClassificationWidget(label="Keywords",),
                   enforceVocabulary=0,
                ),

    StringField('kw',
                default='',
                searchable=0,
                required=0,
                schemata="classification",
                widget=StringWidget(label='kw',
                                    visible = {'view':'invisible',
                                               'edit':'invisible'}),
                enforceVocabulary=0,
                ),
    ))


    
