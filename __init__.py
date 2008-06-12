from AccessControl import allow_module
from AccessControl import ModuleSecurityInfo
from Products.CMFCore.CMFCorePermissions import AddPortalContent
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore import utils as cmfutils
from Products.validation import validation
from config import *

from Products.Archetypes.atapi import process_types, listTypes

registerDirectory(SKINS_DIR, GLOBALS)

from poapi import ClassificationTool, GraphVizTool

ModuleSecurityInfo("zExceptions").declarePublic("NotFound")
allow_module("Products.PloneOntology.utils")
allow_module("re")

import workflow
import proposal
import ctool
import ontology
import keyword
import archive
import graphviztool
import owl

validation.register(keyword.XMLNCNameValidator('isXMLNCName'))
validation.register(keyword.UniqueNameValidator('isUniqueName'))

tools = (ClassificationTool, GraphVizTool)

def initialize(context):
    content_types, constructors, ftis = process_types(
       listTypes(PROJECTNAME),
        PROJECTNAME)

    cmfutils.ToolInit(PROJECTNAME, tools=tools,
                   product_name=PROJECTNAME, icon='tool.gif',
                   ).initialize( context )

    cmfutils.registerIcon(ontology.Ontology,
                       'storage.png', globals())

    cmfutils.registerIcon(ClassificationTool,
                       'tool.png', globals())

    cmfutils.ContentInit(
        PROJECTNAME + ' Content',
        content_types      = content_types,
        permission         = ADD_CONTENT_PERMISSION,
        extra_constructors = constructors,
        fti                = ftis,
        ).initialize(context)
