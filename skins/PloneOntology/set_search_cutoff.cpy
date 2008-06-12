## Script (Python) "set_search_cutoff"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=cutoff=0.1, storage='kw_storage', tool='fdp', types=[], font='', forth=0, back=0
##title=
##

ctool = context.portal_classification
gtool = context.graphviz_tool

ctool.setStorageId(storage)

ctool.setClassifyTypes(types)

try:
    ctool.setSearchCutoff(cutoff)
except ValueError:
    return state.set(portal_status_message='Error: Enter a positive float value.')

changes=0

if forth != ctool.getForth():
    changes=1

if back != ctool.getBack():
    changes=1

if font != ctool.getGVFont():
    changes=1

if tool != gtool.getLayouter():
    changes=1

ctool.setGVFont(font)
ctool.setBack(back)
ctool.setForth(forth)
gtool.setLayouter(tool)

msg = ''
if changes == 1:
    try:
        for el in ctool.getStorage().contentValues('Keyword'):
            msg = msg + el.updateKwMap(levels=2)
    except:
        pass # ignore NotFound exception for silent operation without graphviz
    #    return state.set(portal_status_message='Error: keyword graphs could not be updated.')

if msg:
    return state.set(portal_status_message=msg)
else:
    return state.set(portal_status_message='Properties changed.')
