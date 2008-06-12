## Script (Python) "impOWL"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=file
##title=
##
ctool = context.portal_classification
storage = ctool.getStorage()

msg = storage.importOWL(file)
storage.updateGraphvizMap()

return state.set(portal_status_message='Ontology from %s imported.\n%s' % (file.filename, msg))