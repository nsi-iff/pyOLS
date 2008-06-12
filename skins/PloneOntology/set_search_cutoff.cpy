## Script (Python) "set_search_cutoff"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=cutoff=0.1, storage='kw_storage', tool='fdp', types=[], font=''
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

if font != ctool.getGVFont():
    changes=1

if tool != gtool.getLayouter():
    changes=1

ctool.setGVFont(font)
gtool.setLayouter(tool)

if changes == 1:
    try:
        for el in ctool.getStorage().contentValues('Keyword'):
            el.updateKwMap(levels=2)
    except:
        return state.set(portal_status_message='Error: keyword graphs could not be updated.')

return state.set(portal_status_message='Properties changed.')
