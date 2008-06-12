from Products.Archetypes.atapi import BaseContent, BaseSchema, registerType
from Products.PloneOntology.poapi import ClassificationSchema

from config import *

ceschema = BaseSchema + ClassificationSchema 

class ClassificationExample(BaseContent):
    schema = ceschema
    
registerType(ClassificationExample, PROJECTNAME)
