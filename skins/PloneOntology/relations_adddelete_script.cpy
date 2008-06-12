## Script (Python) "relations_adddelete"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=rel='', dest=''
##title=
##

ctool = context.portal_classification

ctool.addReference(context.getName(), dest, rel)
ctool.getKeyword(context.getName()).updateKwMap()
ctool.getKeyword(dest).updateKwMap()

return state.set(portal_status_message='Successfully added reference.')