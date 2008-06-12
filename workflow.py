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
#first make keyword
kwprop=state_change.object #getattr(context, context.getKPId())
name=kwprop.generateName(kwprop.getKPTitle(),kwprop.getShortAdditionalDescription())

context.portal_classification.manage_addKeyword(name=name, title=kwprop.getKPTitle(), description=kwprop.getPKWDescription(), shortAdditionalDescription=kwprop.getShortAdditionalDescription())
srcFldr = kwprop.aq_parent

#then make relations
storage=context.portal_classification.getStorage()
newkwhandle=context.portal_classification.getKeyword(name)
reflist=kwprop.getRefs()
wf_id="kw_proposal_workflow"
tool=context.portal_workflow

new_kws_list=[]

# retrieve the state
tool.getInfoFor(kwprop, "review_state", None)
for thing in reflist:
 if tool.getInfoFor(thing, "review_state") == "pending":
  try:
   relation_object=context.portal_classification.getKeyword(thing.getSearchKWB())
   id2=relation_object.getName()
   context.portal_classification.addReference(name, id2, thing.getRelation())
  except:
   relation_object=context.portal_classification.getKeywordProposal(thing.getSearchKWB())
   context.portal_classification.manage_addKeyword(name=relation_object.generateName(relation_object.getKPTitle(),relation_object.getShortAdditionalDescription()), title=relation_object.getKPTitle(), description=relation_object.getPKWDescription(), shortAdditionalDescription=relation_object.getShortAdditionalDescription())
   new_kws_list.append(context.portal_classification.getKeyword(relation_object.generateName(relation_object.getKPTitle(),relation_object.getShortAdditionalDescription())))
   context.portal_classification.addReference(name, relation_object.generateName(relation_object.getKPTitle(), relation_object.getShortAdditionalDescription()), thing.getRelation())
 tool.doActionFor(thing, "approve", comment="")

#graphviz support
new_kws_list.append(newkwhandle)

for obj in new_kws_list:
 innernodes = obj.getRefs() or [] #level 1 keywords
 nodes = []
 [nodes.extend(x.getRefs() or []) for x in innernodes]
 outernodes= [] #level 2 keywords
 [outernodes.append(x) for x in nodes if not (x in outernodes or x in innernodes or x == obj)]
 try:
  obj.updateKwMap(levels=2)
  for node in innernodes:
   node.updateKwMap(levels=2)
  for node in outernodes:
   node.updateKwMap(levels=2)
 except:
  pass

stay=kwprop.getId()
context.portal_url.getPortalObject().accepted_kws.manage_pasteObjects(kwprop.getParentNode().manage_cutObjects(kwprop.getId()))

raise state_change.ObjectMoved(getattr(context.portal_url.getPortalObject().accepted_kws, stay), srcFldr) 

return ''
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
#this script shall make all the referenced relationproposals of the keywordproposal to move alond with it through the workflow
tool=context.portal_workflow
try:
 src_obj=getattr(context, context.getKPId())
except:
 src_obj=state_change.object
for thing in src_obj.getRefs():
 tool.doActionFor(thing, "submit", comment="")
return ""
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
#this script shall make all the referenced relationproposals of the keywordproposal to move along with it through the workflow
tool=context.portal_workflow
try:
 src_obj=getattr(context, context.getKPId())
except:
 src_obj=state_change.object
for thing in src_obj.getRefs():
 tool.doActionFor(thing, "reject", comment="")
return ""
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
relprop=state_change.object
relid=relprop.getId()
srcFldr = relprop.aq_parent
storage=context.portal_classification.getStorage()
one=0
new_kws_list=[]
try:
 kwobj=context.portal_classification.getKeyword(relprop.getSearchKWA())
 id=kwobj.getName()
except:
 proposalobj=context.portal_classification.getKeywordProposal(relprop.getSearchKWA())
 context.portal_classification.manage_addKeyword(name=proposalobj.generateName(proposalobj.getKPTitle(),proposalobj.getShortAdditionalDescription()), title=proposalobj.title_or_id(), shortAdditionalDescription=proposalobj.getShortAdditionalDescription(), description=proposalobj.getKeywordProposalDescription())
 kwobj=context.portal_classification.getKeyword(name=proposalobj.generateName(proposalobj.getKPTitle(),proposalobj.getShortAdditionalDescription()))
 id=kwobj.getName()

try:
 relation_object=context.portal_classification.getKeyword(relprop.getSearchKWB())
except:
 proposalobj=context.portal_classification.getKeywordProposal(relprop.getSearchKWB())
 context.portal_classification.manage_addKeyword(name=proposalobj.generateName(proposalobj.getKPTitle(),proposalobj.getShortAdditionalDescription()), title=proposalobj.title_or_id(), shortAdditionalDescription=proposalobj.getShortAdditionalDescription(), description=proposalobj.getKeywordProposalDescription())
 relation_object=context.portal_classification.getKeyword(name=proposalobj.generateName(proposalobj.getKPTitle(),proposalobj.getShortAdditionalDescription()))
try:
 newcontext=getattr(context, relation_object.getId())
 if relation_object.meta_type == 'KeywordProposal':
  context.portal_classification.manage_addKeyword(name=newcontext.generateName(newcontext.getKPTitle(),newcontext.getShortAdditionalDescription()), title=newcontext.getKPTitle(), description=newcontext.getPKWDescription(), shortAdditionalDescription=newcontext.getShortAdditionalDescription())
  new_kws_list.append(getattr(storage, newcontext.generateName(newcontext.getKPTitle(),newcontext.getShortAdditionalDescription())))
  context.portal_classification.addReference(id, relation_object.generateName(newcontext.getKPTitle(),newcontext.getShortAdditionalDescription()), relprop.getRelation())
except:
 if relation_object.meta_type != 'KeywordProposal':
  id2=relation_object.getName()
  context.portal_classification.addReference(id, id2, relprop.getRelation())

if relprop.getParentNode().meta_type != 'KeywordProposal':
    context.portal_url.getPortalObject().accepted_kws.manage_pasteObjects(relprop.manage_cutObjects(relid))
    one=1
newkwhandle=context.portal_classification.getKeyword(id)

#graphviz support
new_kws_list.append(newkwhandle)
for obj in new_kws_list:
 innernodes = obj.getRefs() or [] #level 1 keywords
 nodes = []
 [nodes.extend(x.getRefs() or []) for x in innernodes]
 outernodes= [] #level 2 keywords
 [outernodes.append(x) for x in nodes if not (x in outernodes or x in innernodes or x == obj)]

 try:
  obj.updateKwMap(levels=2)
 except:
  pass

 for node in innernodes:
   try:
     node.updateKwMap(levels=2)
   except:
     pass

 for node in outernodes:
   try:
     node.updateKwMap(levels=2)
   except:
     pass

if one==1:
 raise state_change.ObjectMoved(getattr(context.portal_url.getPortalObject().accepted_kws, relid), srcFldr) 
return ""
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

