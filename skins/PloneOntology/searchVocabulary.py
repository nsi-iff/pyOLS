## Script (Python) "searchVocabulary"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=field='', searchTerm='', categories=[]

field2=''
if field=='SearchKWA':
    items = context.portal_classification.searchMatchingKeywordsFor(context, search=searchTerm, search_kw_proposals='true', search_linked_keywords='true')
elif field=='SearchKWB':
    items = context.portal_classification.searchMatchingKeywordsFor(context, search=searchTerm, search_kw_proposals='true', search_linked_keywords='true')
elif field=='kw_search':
    items = context.portal_classification.searchMatchingKeywordsFor(context, search=searchTerm, search_kw_proposals='false', search_linked_keywords='true')
else:
    items = context.portal_classification.searchMatchingKeywordsFor(context, search=searchTerm, search_kw_proposals='false', search_linked_keywords='true')

context.REQUEST.response.setHeader('Content-Type', 'text/html; charset=%s' % context.portal_classification.getEncoding())

#categories = context.getCategories()
value = '''
<html><body>
<h1 class="hiddenStructure">%s</h1>
<ul style="background-color:#ffffdd; border: 1px solid; list-style-position: inside; width: auto">
''' % field

for x in items:
    if field == 'title':
        name = x.Title()
    elif x.meta_type == "KeywordProposal":
        name = x.generateName(x.getKPTitle(), x.getShortAdditionalDescription())
    else:
        name = x.getName()
    value = value + """<li style="padding-left: 1em"><a href="javascript:void setInput('%s', '%s')">%s</a></li>""" % (field, name, x.title_or_id())

value = value + "\n</ul></body></html>"

return value

