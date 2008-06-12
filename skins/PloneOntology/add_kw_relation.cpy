## Script (Python) "add_kw_relation"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=id,factor=1
##title=Classification handler
##

ctool = context.portal_classification
ctool.addRelation(id, factor)

return state.set(portal_status_message='New keyword relation added.')

