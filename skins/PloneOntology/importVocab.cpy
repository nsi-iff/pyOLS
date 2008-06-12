## Script (Python) "importVocab"
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

storage.importVocabulary(file)
storage.updateGraphvizMap()

return state.set(portal_status_message='Ontology from %s imported.' % file.filename)