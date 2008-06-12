## Script (Python) "classify"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=keyword
##title=
##
kwobj = context.portal.kw_storage[keyword]

context.addReference(kwobj, 'classifiedAs')
