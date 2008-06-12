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

from Products.Relations.exception import ValidationException

ctool = context.portal_classification
try:
    ctool.addRelation(id, factor)
except ValidationException:
    return state.set(portal_status_message='Name has to be an XML NCName (e.g. no spaces).')
except NameError:
    return state.set(portal_status_message='Name already exists.')

return state.set(portal_status_message='New keyword relation added.')

