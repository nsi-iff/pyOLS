## Script (Python) "del_kw_relation"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=ids=[]
##title=
##

ctool = context.portal_classification

if ids:
    for id in ids:
        ctool.delRelation(id)

    return state.set(portal_status_message='Removed selected relations.')

return state.set(portal_status_message='No relations selected for removal.')

