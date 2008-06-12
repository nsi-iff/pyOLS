"""Custom widgets for this project
"""

from Products.Archetypes.Widget import TypesWidget
from Products.Archetypes.atapi import *
from Products.CMFCore.utils import getToolByName
from AccessControl import ClassSecurityInfo
from Products.Archetypes.Registry import registerWidget,registerPropertyType

class ActiveStringWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "activestring",
        'helper_js' : ('sarissa.js','activestring.js', 'sarissa_ieemu_xpath.js'),
        'size' : '30',
        'dataurl' : 'string:${here/absolute_url}/searchVocabulary?field=${fieldName}',
        })

    security = ClassSecurityInfo()

registerWidget(ActiveStringWidget,
               title='Active String Widget',
               description=('A String widget that will auto-complete the value you type.'),
               used_for=('Products.Archetypes.Field.StringField',)
               )

registerPropertyType('dataurl', 'string', ActiveStringWidget)

class RelationRefWidget(ReferenceWidget):
    _properties = ReferenceWidget._properties.copy()
    _properties.update({
        'macro' : "relation_ref_widget",
        })

class SearchKWAWidget(ActiveStringWidget):
    _properties = ActiveStringWidget._properties.copy()
    _properties.update({
        'macro' : "activestringa",
        })

class SearchKWBWidget(ActiveStringWidget):
    _properties = ActiveStringWidget._properties.copy()
    _properties.update({
        'macro' : "activestringb",
        })
