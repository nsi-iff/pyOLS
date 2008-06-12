## Script (Python) "exportVocab"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=
##
ctool = context.portal_classification
storage = ctool.getStorage()

return storage.exportVocabulary()