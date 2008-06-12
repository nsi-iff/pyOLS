## Script (Python) "updateMap"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=
##

try:
        msg = context.updateKwMap(levels=2)
except:
        pass # ignore NotFound exception for silent operation without graphviz
    #    return state.set(portal_status_message='Error: keyword graphs could not be updated.')

if msg:
    return state.set(portal_status_message=msg)
else:
    return state.set(portal_status_message='Properties changed.')
