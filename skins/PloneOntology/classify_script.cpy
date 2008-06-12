## Script (Python) "classify_script"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=keywords=[], exkeywords=[],
##title=Classification handler
##

kw_search = context.REQUEST.get('form.button.kw_search',None)
del_ref = context.REQUEST.get('form.button.del_ref',None)
add_ref = context.REQUEST.get('form.button.add_ref',None)
active_search_result = context.REQUEST.get('kw_active_search',None)

if add_ref:
    kws=''
    for el in keywords:
     if el not in exkeywords:
        kws=kws+el+', '
        storage = context.portal_classification.getStorage()
        keyword = getattr(storage, el)
        newUID = keyword.UID()
	context.reference_catalog.addReference(context, newUID, 'classifiedAs')
    return state.set(portal_status_message='added referneces: ' + kws)

if del_ref:
    kws=''
    for el in exkeywords:
        kws=kws+el+', '
        storage = context.portal_classification.getStorage()
        keyword = getattr(storage, el)
        newUID = keyword.UID()
	context.reference_catalog.deleteReference(context, newUID, 'classifiedAs')
    return state.set(portal_status_message='removed following referneces: ' + kws)



if kw_search:
   if active_search_result != '' and active_search_result != None:
	context.reference_catalog.addReference(context, active_search_result, 'classifiedAs')
        return state.set(portal_status_message='added refernece')

   else:
        return state.set()
 
