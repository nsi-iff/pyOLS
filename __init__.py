# -*- coding: UTF-8 -*-

##################################################
#                                                
#    Copyright (C), 2004, 2005 Thomas F�rster         
#    <t.foerster@biologie.hu-berlin.de>          
#
#    Humboldt University of Berlin               
#                                                
##################################################

from Products.CMFCore.CMFCorePermissions import AddPortalContent
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore import utils as cmfutils
from config import *

from Products.Archetypes.atapi import process_types, listTypes

registerDirectory(SKINS_DIR, GLOBALS)

from poapi import ClassificationTool, GraphVizTool

import workflow
import proposal
import ctool
import ontology
import keyword
import archive
import graphviztool

import example

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
