## Script (Python) "searchVocabulary"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=field, searchTerm='', categories=[]

#possibleItems = ('small car', 'large car', 'small truck', 'large truck', 'van', 'suv')


## for el in context.portal_classification.searchMatchingKeywordsFor(context, search=searchTerm, search_kw_proposals='true', search_linked_keywords='false'):
##     items.append(el.title_or_id())

#for x in possibleItems:
#    if x.find(searchTerm) > -1:
#        items.append(x)

field2=''
if field=='SearchKWA':
    field2='KeywordA'
    items = context.portal_classification.searchMatchingKeywordsFor(context, search=searchTerm, search_kw_proposals='true', search_linked_keywords='false')
elif field=='SearchKWB':
    field2='KeywordB'
    items = context.portal_classification.searchMatchingKeywordsFor(context, search=searchTerm, search_kw_proposals='true', search_linked_keywords='false')
else:
    field2= 'skw'
    items = context.portal_classification.searchMatchingKeywordsFor(context, search=searchTerm, search_kw_proposals='false', search_linked_keywords='false')

#categories = context.getCategories()
value = '''
<html><body>
<h1 class="hiddenStructure">%s</h1>
<ul style="background-color:#ffffdd; border: 1px solid; list-style-position: inside; width: auto">
''' % field

if field=='title':
  for x in items:
     value = value + """<li style="padding-left: 1em"><a href="javascript:void setInput('%s', '%s')">%s</a></li>""" % (field, x.Title(), x.title_or_id())
else:
 for x in items:
    value = value + '''<li style="padding-left: 1em"><a href="javascript:void setInput('%s', '%s');void setInput('%s', '%s')">%s</a></li>''' % (field, x.title_or_id(), field2, x.UID(), x.title_or_id())

value = value + "\n</ul></body></html>"

return value

