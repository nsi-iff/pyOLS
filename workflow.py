from Products.PythonScripts.PythonScript import PythonScript
from Products.CMFCore.CMFCorePermissions import ModifyPortalContent, View, \
     AccessContentsInformation, RequestReview, ReviewPortalContent
from Products.CMFCore.WorkflowTool import addWorkflowFactory
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.DCWorkflow.Default import setupDefaultWorkflowClassic

p_access = AccessContentsInformation
p_modify = ModifyPortalContent
p_view = View
p_review = ReviewPortalContent
p_request = RequestReview

def setupKeywordProposalWorkflow(wf):
    # nothing but the 'old' default worflow
    setupDefaultWorkflowClassic(wf)

    # add custom states and transitions
    wf.states.addState('approved')
    wf.states.deleteStates(['published'])

    wf.transitions.addTransition('approve')
    wf.transitions.deleteTransitions(['publish','retract'])

    # and configure them
    new_state = wf.states['approved']
    new_state.setProperties(
        title='',
        transitions=('',)
        )
    new_state.setPermission(p_access , 1, ())
    new_state.setPermission(p_view , 1, ())
    new_state.setPermission(p_modify , 0, ())

    pending_state = wf.states['pending']
    pending_state.setProperties(
        title='',
        transitions=('approve','reject')
        )

    new_trans = wf.transitions['approve']
    new_trans.setProperties(
        title='Keyword Reviewer approves keyword_proposal',
        new_state_id='approved',
        after_script_name='generateKeyword',
        actbox_name='Approve',
        actbox_url='%(content_url)s/content_publish_form',
        props={'guard_permissions':p_review},
        )

    submit_trans = wf.transitions['submit']
    submit_trans.setProperties(
        title='Member requests publishing',
        new_state_id='pending',
        actbox_name='Submit',
        actbox_url='%(content_url)s/content_submit_form',
        props={'guard_permissions':p_request},
        after_script_name='submitRelations',
        )

    reject_trans = wf.transitions['reject']
    reject_trans.setProperties(
        title='Reviewer rejects submission',
        new_state_id='private',
        actbox_name='Reject',
        actbox_url='%(content_url)s/content_reject_form',
        props={'guard_permissions':p_review},
        after_script_name='rejectRelations',
        )

def addScript(wf):
    """
    add a script for triggering Keyword creation
    """
    myscript = PythonScript('generateKeyword')
    myscript.write(
'''## Script (Python) "generateKeyword"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##


from Products.Relations.exception import ValidationException

# create keyword from proposal
kwProp  = state_change.object
kwTitle = kwProp.getKPTitle()
kwDesc  = kwProp.getKeywordProposalDescription()
kwSAD   = kwProp.getShortAdditionalDescription()
kwName  = kwProp.generateName(kwTitle, kwSAD)
#try:
kw      = context.portal_classification.addKeyword(kwName, kwTitle, kwDesc, kwSAD)
#except ValidationException:
#    state_change.getPortal().state.set(portal_status_message="'%s' is not a valid XML NCName" % kwName)
#    return
#except NameError:
#    state_change.getPortal().state.set(portal_status_message="'%s' already exists in current ontology" % kwName)
#    return
#except AttributeError:
#    pass

# approve all referenced relation proposals
wfTool = context.portal_workflow
for refProp in kwProp.getRefs('hasRelation'):
    if wfTool.getInfoFor(refProp, "review_state") == "pending":
        wfTool.doActionFor(refProp, "approve", commtent="")

kw.updateKwMap()

accepted_kws = context.portal_url.getPortalObject().accepted_kws
kwPropId     = kwProp.getId()
accepted_kws.manage_pasteObjects(kwProp.getParentNode().manage_cutObjects(kwPropId))
raise state_change.ObjectMoved(getattr(accepted_kws, kwPropId), kwProp.aq_parent)
'''
)

    script_folder = getattr(wf, 'scripts')
    if script_folder:
        script_folder._setObject("generateKeyword", myscript)


def addScript2(wf):
    """
    add a script for triggering Keyword creation
    """
    myscript = PythonScript('submitRelations')
    myscript.write(
'''## Script (Python) "submitRelations"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##

# this script shall make all the referenced relationproposals of the keywordproposal to move along with it through the workflow

for refProp in state_change.object.getRefs('hasRelation'):
    context.portal_workflow.doActionFor(refProp, "submit", comment="")
'''
)

    script_folder = getattr(wf, 'scripts')
    if script_folder:
        script_folder._setObject("submitRelations", myscript)

def addScript3(wf):
    """
    add a script for triggering Keyword creation
    """
    myscript = PythonScript('rejectRelations')
    myscript.write(
'''## Script (Python) "rejectRelations"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##

# this script shall make all the referenced relationproposals of the keywordproposal to move along with it through the workflow

for refProp in state_change.object.getRefs('hasRelation'):
    context.portal_workflow.doActionFor(refProp, "reject", comment="")
'''
)

    script_folder = getattr(wf, 'scripts')
    if script_folder:
        script_folder._setObject("rejectRelations", myscript)

def createKeywordProposalWorkflow(id):
    ob=DCWorkflowDefinition(id)
    setupKeywordProposalWorkflow(ob)
    ob.setProperties(title='KeywordProposalWorkflow [PloneOntology]')
    addScript(ob)
    addScript2(ob)
    addScript3(ob)
    return ob

addWorkflowFactory( createKeywordProposalWorkflow, id='keyword_proposal_workflow'
                  , title='KeywordProposalWorkflow [PloneOntology]')

def setupRelationProposalWorkflow(wf):
    # nothing but the 'old' default worflow
    setupDefaultWorkflowClassic(wf)

    # add custom states and transitions
    wf.states.addState('approved')
    wf.states.deleteStates(['published'])

    wf.transitions.addTransition('approve')
    wf.transitions.deleteTransitions(['publish','retract'])

    # and configure them
    new_state = wf.states['approved']
    new_state.setProperties(
        title='',
        transitions=('',)
        )
    new_state.setPermission(p_access , 1, ())
    new_state.setPermission(p_view , 1, ())
    new_state.setPermission(p_modify , 0, ())

    pending_state = wf.states['pending']
    pending_state.setProperties(
        title='',
        transitions=('approve','reject')
        )

    new_trans = wf.transitions['approve']
    new_trans.setProperties(
        title='Keyword Reviewer approves relation_proposal',
        new_state_id='approved',
        after_script_name='generateRelation',
        actbox_name='Approve',
        actbox_url='%(content_url)s/content_publish_form',
        props={'guard_permissions':p_review},
        )

def addScript4(wf):
    """
    add a script for triggering Relation creation
    """
    myscript = PythonScript('generateRelation')
    myscript.write(
'''## Script (Python) "generateRelation"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##

from zExceptions import NotFound
from Products.Relations.exception import ValidationException

wfTool           = context.portal_workflow
relationProposal = state_change.object
srcName          = relationProposal.getSearchKWA()
dstName          = relationProposal.getSearchKWB()
relation         = relationProposal.getRelation()

try:
    srcKP = context.portal_classification.getKeywordProposal(srcName)
    if wfTool.getInfoFor(srcKP, "review_state") == "private":
        wfTool.doActionFor(srcKP, "submit", comment="")
    if wfTool.getInfoFor(srcKP, "review_state") == "pending":
        wfTool.doActionFor(srcKP, "approve", comment="")
except NotFound:
    pass

try:
    dstKP = context.portal_classification.getKeywordProposal(dstName)
    if wfTool.getInfoFor(dstKP, "review_state") == "private":
        wfTool.doActionFor(dstKP, "submit", comment="")
    if wfTool.getInfoFor(dstKP, "review_state") == "pending":
        wfTool.doActionFor(dstKP, "approve", comment="")
except NotFound:
    pass

context.portal_classification.addReference(srcName, dstName, relation)
context.portal_classification.getKeyword(srcName).updateKwMap()
context.portal_classification.getKeyword(dstName).updateKwMap()

if not relationProposal.hasKeywordProposal():
    accepted_kws = context.portal_url.getPortalObject().accepted_kws
    relPropId    = relationProposal.getId()
    accepted_kws.manage_pasteObjects(relationProposal.getParentNode().manage_cutObjects(relPropId))
    raise state_change.ObjectMoved(getattr(accepted_kws, relPropId), relationProposal.aq_parent)
'''
)

    script_folder = getattr(wf, 'scripts')
    if script_folder:
        script_folder._setObject("generateRelation", myscript)


def createRelationProposalWorkflow(id):
    ob=DCWorkflowDefinition(id)
    setupRelationProposalWorkflow(ob)
    ob.setProperties(title='RelationProposalWorkflow [PloneOntology]')
    addScript4(ob)
    return ob

addWorkflowFactory( createRelationProposalWorkflow, id='relation_proposal_workflow'
                  , title='RelationProposalWorkflow [PloneOntology]')

