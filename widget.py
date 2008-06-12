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

class ClassificationWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widget_classification",
        })
    
class SearchKWWidget(ActiveStringWidget):
    _properties = ActiveStringWidget._properties.copy()
    _properties.update({
        'macro' : "activestringkw",
        })
    security = ClassSecurityInfo()
    security.declarePublic('process_form')
    def process_form(self, instance, field, form, empty_marker=None,
                     emptyReturnsMarker=False):
        """
        Basic impl for form processing in a widget
        """
        #my changes
        at=getToolByName(instance, 'archetype_tool', None)
        try:
            try:
                val = instance.getCategories()
            except:
                val=[]
            val.append(at.lookupObject(form['skw']))
            instance.setCategories(val)
        except:
            pass
        #original
        value = form.get(field.getName(), empty_marker)
        if value is empty_marker:
            return empty_marker
        if emptyReturnsMarker and value == '':
            return empty_marker
        return value, {}

class MyRefWidget(ReferenceWidget):
    _properties = ReferenceWidget._properties.copy()
    _properties.update({
        'macro' : "my_ref_widget",
        })

class ExistingKeywordsWidget(StringWidget):
    _properties = StringWidget._properties.copy()
    _properties.update({
        'macro' : "ex_kw_widget",
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

class KWAWidget(StringWidget):
    _properties = StringWidget._properties.copy()
    _properties.update({
        'macro' : "kwa_string_widget",
        })

class KWBWidget(StringWidget):
    _properties = StringWidget._properties.copy()
    _properties.update({
        'macro' : "kwb_string_widget",
        })

