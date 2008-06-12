from StringIO import StringIO

from Products.PloneOntology.config import *
from Products.PloneOntology.poapi import ProposalArchive

from Products.PythonScripts.PythonScript import PythonScript
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.public import listTypes
from Products.Archetypes.Extensions.utils import installTypes, install_subskin
from Products.CMFFormController.FormAction import FormAction, FormActionKey

def checkDependencies(portal, out):
    """Check whether dependency products are installed"""

    qi = getToolByName(portal, "portal_quickinstaller")

    ok = True

    for d in DEPENDENCIES:
        if not qi.isProductInstalled(d[0]):
            ok = False
            out.write("Product '%s' is missing (see %s).\n" % d)

    if not ok:
        raise "DEPENDENCY PRODUCTS ARE MISSING\n\n %s" % out.getvalue()

def setupTool(portal, out):
    """
    adds the tool to the portal root folder
    creates kw_storage if necessary
    """
    try:
        ctool = getToolByName(portal, 'portal_classification')
    except AttributeError:
        ctool = None

    cltypes = []

    if ctool is not None:
        # save settings
        try:
            cltypes = ctool.getClassifyTypes()
        except AttributeError:
            pass

        portal.manage_delObjects(['portal_classification'])
        out.write('Deleting old classification tool')

    addTool = portal.manage_addProduct[PROJECTNAME].manage_addTool
    addTool('Classification Tool', None)
    ctool = getToolByName(portal, 'portal_classification')

    ctool.setClassifyTypes(cltypes)
    out.write("\nAdded the classification tool to the portal root folder.\n")

    if hasattr(portal, 'graphviz_tool'):
        portal.manage_delObjects(['graphviz_tool'])
        out.write('Deleting old graphviz tool')

    addTool('GraphViz Tool', None)

    out.write("\nAdded the graphviz tool to the portal root folder.\n")


def registerConfiguration(portal, out):
    portal_conf=getToolByName(portal,'portal_controlpanel')
    portal_conf.registerConfiglet( PROJECTNAME
                                   , PROJECTNAME
                                   , 'string:${portal_url}/configure_tool_properties' 
                                   , ''                   # a condition   
                                   , 'Manage portal'      # access permission
                                   , 'Products'           # section to which the configlet should be added: 
                                   #(Plone,Products,Members) 
                                   , 1                    # visibility
                                   , PROJECTNAME
                                   , 'po_configlet.gif' # icon in control_panel, put your own icon in the 
                                   # /skins folder of your product and change 
                                   #'site_icon.gif' to 'yourfile'
                                   , 'Sitewide configuration of the classification tool'
                                   , None
                                   )

def addClassifyAction(portal):
    at=getToolByName(portal, 'portal_actions')

    at.addAction('classify',
                 name='Classify',
                 action='string:${object_url}/classify_form',
                 condition='python:(portal.reference_catalog.isReferenceable(object) and object.meta_type in portal.portal_classification.getClassifyTypes())',
                 permission='Modify portal content',
                 category='object_tabs')

def addCustomFormControllerTransitions(portal, out):
    # st = getToolByName(portal, 'portal_skins')
    # pt = st.archetypes.base_edit
    container = getToolByName(portal, 'portal_form_controller')

    container.addFormAction('relations_adddelete', 'success','',
                            'Save', 'traverse_to',
                            'string:updateMap')
    container.addFormAction('relations_adddelete', 'failure','',
                            'Save', 'traverse_to',
                            'string:updateMap')
    container.addFormAction('base_edit', 'success','',
                            'search', 'traverse_to',
                            'string:base_edit')
    container.addFormAction('base_edit', 'success','',
                            'search2', 'traverse_to',
                            'string:base_edit')
    container.addFormAction('base_edit', 'success','',
                            'search3', 'traverse_to',
                            'string:classification_edit')
    container.addFormAction('base_edit', 'failure','',
                            'search4', 'traverse_to',
                            'string:classification_edit')
    container.addFormAction('base_edit', 'failure','',
                            'search5', 'traverse_to',
                            'string:classification_edit')
    container.addFormAction('base_edit', 'success','',
                            'search4', 'traverse_to',
                            'string:classification_edit')
    container.addFormAction('base_edit', 'success','',
                            'search5', 'traverse_to',
                            'string:classification_edit')
    container.addFormAction('base_edit', 'success','',
                             'add', 'traverse_to',
                             'string:classification_edit')
    container.addFormAction('base_edit', 'success','',
                             'delete', 'traverse_to',
                             'string:classification_edit')
    container.addFormAction('base_edit', 'success','',
                             'sel', 'traverse_to',
                             'string:classification_edit')
    container.addFormAction('base_edit', 'success','',
                             'sel2', 'traverse_to',
                             'string:classification_edit')
    container.addFormAction('base_edit', 'failure','',
                             'sel2', 'traverse_to',
                             'string:classification_edit')
    container.addFormAction('base_edit', 'success','',
                             'sel3', 'traverse_to',
                             'string:classification_edit')
    container.addFormAction('base_edit', 'failure','',
                             'sel3', 'traverse_to',
                             'string:classification_edit')
    container.addFormAction('base_edit', 'success','',
                             'add_search', 'traverse_to',
                             'string:classification_edit')

def removeCustomFormControllerTransitions(portal, out):
    fc = getToolByName(portal, 'portal_form_controller')
    #BAAH no Python API for deleting actions in FormController
    #lets get our hands dirty
    container = fc.actions
    try:
        container.delete(FormActionKey('relations_adddelete', 'success','',
                            'Save', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('relations_adddelete', 'failure','',
                            'Save', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'search', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'search2', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'delete', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'add', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'search3', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'search4', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'search5', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'sel', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'sel2', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'sel3', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'failure', '',
                                       'sel3', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'failure', '',
                                       'search4', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'failure', '',
                                       'search5', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'failure', '',
                                       'sel2', fc))
    except KeyError: pass
    try:
        container.delete(FormActionKey('base_edit', 'success', '',
                                       'add_search', fc))
    except KeyError: pass

def setupKeywordProposalWorkflow(portal, out):
    """the proposal wf"""
    wf_tool = getToolByName(portal, 'portal_workflow')
    wf_tool.manage_addWorkflow( id='keyword_proposal_workflow',
                                workflow_type='keyword_proposal_workflow '+\
                                '(KeywordProposalWorkflow [PloneOntology])'
                                )
#    wf_tool.setChainForPortalTypes('KeywordProposal', 'kw_proposal_workflow ')
    out.write("Set up KeywordProposalWorkflow")

def setupRelationProposalWorkflow(portal, out):
    """the proposal wf II"""
    wf_tool = getToolByName(portal, 'portal_workflow')
    wf_tool.manage_addWorkflow( id='relation_proposal_workflow',
                                workflow_type='relation_proposal_workflow (RelationProposalWorkflow [PloneOntology])'
                                )
#    wf_tool.setChainForPortalTypes('KeywordProposal', 'kw_proposal_workflow ')
    out.write("Set up RelationProposalWorkflow")

def addArchive(portal, out):
    """ the kw proposal storage """
    try:
        pt=getToolByName(portal, 'portal_types')
        pt.getTypeInfo('ProposalArchive').global_allow=True
        portal.invokeFactory('ProposalArchive', id = 'accepted_kws',
                             title='Accepted KW Proposals',)
        getattr(portal, 'accepted_kws')._updateProperty('exclude_from_nav', 1)
        getToolByName(portal, 'portal_catalog').reindexObject(getattr(portal, 'accepted_kws'))
        pt.getTypeInfo('ProposalArchive').global_allow=False
        out.write("Set up Proposal Archive.\n")
    except:
        out.write("Couldn't setup proposal archive.\n")

def install(portal):
    out = StringIO()
    checkDependencies(portal, out)
    setupKeywordProposalWorkflow(portal, out)
    setupRelationProposalWorkflow(portal, out)
    installTypes(portal, out, listTypes(PROJECTNAME), PROJECTNAME, GLOBALS)
    addArchive(portal, out)
    addClassifyAction(portal)
    setupTool(portal, out)
    wf_tool = getToolByName(portal, 'portal_workflow')
    wf_tool.setChainForPortalTypes(('KeywordProposal',), 'keyword_proposal_workflow ')
    wf_tool.setChainForPortalTypes(('Keyword',), '(Default)')
    wf_tool.setChainForPortalTypes(('RelationProposal',), 'relation_proposal_workflow ')
    registerConfiguration(portal, out)
    addCustomFormControllerTransitions(portal, out)

    # Make name field searchable
    cat_tool = getToolByName(portal, 'portal_catalog')
    if 'name' not in cat_tool.indexes():
        cat_tool.addIndex('name', 'FieldIndex')
    if 'name' not in cat_tool.schema():
        cat_tool.addColumn('name')

    return out.getvalue()

def uninstall(portal):
    out = StringIO()
    portal_conf=getToolByName(portal,'portal_controlpanel')
    portal_conf.unregisterConfiglet(PROJECTNAME)
    removeCustomFormControllerTransitions(portal, out)

    return out.getvalue()
