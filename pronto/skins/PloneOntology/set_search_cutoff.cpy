## Script (Python) "set_search_cutoff"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=cutoff=0.1, storage='kw_storage', classify, tool='fdp', types=[], font='', relfont='', forth=1, back=0, fontpath='', focus_nodeshape = 'ellipse', focus_nodecolor = '#eeeeee', focus_node_font_color = '#000000', focus_node_font_size = 9, first_nodeshape = 'box', first_nodecolor = 'transparent', first_node_font_color = '#000000', first_node_font_size = 8, second_nodeshape = 'box', second_nodecolor = 'transparent', second_node_font_color = '#000000', second_node_font_size = 7, edgeshape = 'normal', edgecolor = '#000000', edge_font_color = '#111111', edge_font_size = 8
##title=
##

ctool = context.portal_classification
gtool = context.graphviz_tool

updateMap = False
if focus_nodeshape        != ctool.getFocusNodeShape():
    updateMap = True
if first_nodeshape        != ctool.getFirstNodeShape():
    updateMap = True
if second_nodeshape       != ctool.getSecondNodeShape():
    updateMap = True
if edgeshape              != ctool.getEdgeShape():
    updateMap = True
if forth                  != ctool.getForth():
    updateMap = True
if back                   != ctool.getBack():
    updateMap = True
if font                   != ctool.getGVFont():
    updateMap = True
if relfont                != ctool.getRelFont():
    updateMap = True
if tool                   != gtool.getLayouter():
    updateMap = True
if focus_nodecolor        != ctool.getFocusNodeColor():
    updateMap = True
if focus_node_font_color  != ctool.getFocusNodeFontColor():
    updateMap = True
if focus_node_font_size   != ctool.getFocusNodeFontSize():
    updateMap = True
if first_nodecolor        != ctool.getFirstNodeColor():
    updateMap = True
if first_node_font_color  != ctool.getFirstNodeFontColor():
    updateMap = True
if first_node_font_size   != ctool.getFirstNodeFontSize():
    updateMap = True
if second_nodecolor       != ctool.getSecondNodeColor():
    updateMap = True
if second_node_font_color != ctool.getSecondNodeFontColor():
    updateMap = True
if second_node_font_size  != ctool.getSecondNodeFontSize():
    updateMap = True
if edgecolor              != ctool.getEdgeColor():
    updateMap = True
if edge_font_color        != ctool.getEdgeFontColor():
    updateMap = True
if edge_font_size         != ctool.getEdgeFontSize():
    updateMap = True

ctool.setStorageId(storage)
ctool.setClassifyRelationship(classify)
ctool.setClassifyTypes(types)
try:
    ctool.setSearchCutoff(cutoff)
except ValueError:
    return state.set(portal_status_message='Error: Enter a positive float value.')
ctool.setFocusNodeColor(focus_nodecolor)
ctool.setFocusNodeFontColor(focus_node_font_color)
ctool.setFocusNodeFontSize(focus_node_font_size)
ctool.setFirstNodeColor(first_nodecolor)
ctool.setFirstNodeFontColor(first_node_font_color)
ctool.setFirstNodeFontSize(first_node_font_size)
ctool.setSecondNodeColor(second_nodecolor)
ctool.setSecondNodeFontColor(second_node_font_color)
ctool.setSecondNodeFontSize(second_node_font_size)
ctool.setEdgeColor(edgecolor)
ctool.setEdgeFontColor(edge_font_color)
ctool.setEdgeFontSize(edge_font_size)
ctool.setFocusNodeShape(focus_nodeshape)
ctool.setFirstNodeShape(first_nodeshape)
ctool.setSecondNodeShape(second_nodeshape)
ctool.setEdgeShape(edgeshape)
ctool.setFontPath(fontpath)
ctool.setGVFont(font)
ctool.setRelFont(relfont)
ctool.setBack(back)
ctool.setForth(forth)
gtool.setLayouter(tool)

msg = ''
if updateMap:
    try:
        for el in ctool.getStorage().contentValues('Keyword'):
            msg = msg + el.updateKwMap(levels=2)
    except:
        pass # ignore NotFound exception for silent operation without graphviz
    #    return state.set(portal_status_message='Error: keyword graphs could not be updated.')
    ctool.getStorage().updateGraphvizMap()

if msg:
    return state.set(portal_status_message=msg)
else:
    return state.set(portal_status_message='Properties changed.')
