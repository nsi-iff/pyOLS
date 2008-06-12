## Script (Python) "classification_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=keywords=[], kw=None, delKeywords=None, searchterm='', keyworda='', keywordb='', SearchKW='',SearchKWA='', SearchKWB='', skw='',
##title=Classification handler
##

add_button = context.REQUEST.get('form.button.add',None)
del_button = context.REQUEST.get('form.button.delete',None)
se3_button = context.REQUEST.get('form.button.search3',None)
se4_button = context.REQUEST.get('form.button.search4',None)
se5_button = context.REQUEST.get('form.button.search5',None)
sel_button = context.REQUEST.get('form.button.sel',None)
sel2_button = context.REQUEST.get('form.button.sel2',None)
sel3_button = context.REQUEST.get('form.button.sel3',None)
add_search_button = context.REQUEST.get('form.button.add_search',None)

if add_button:
    if keywords is not None:
        storage = context.portal_classification.getStorage()
        
        keywords = [getattr(storage, kw) for kw in keywords]
        newUID = [x.UID() for x in keywords]
        
        val = context.getCategories()
        val.extend(newUID)
        context.setCategories(val)
        
        return state.set(portal_status_message='Selected keywords added.')
    else:
        return state.set(portal_status_message='No keywords selected.')

if add_search_button:
 if skw=='':
  return state.set()
 else:
  storage = context.portal_classification.getStorage()
  val = context.getCategories()
  val.append(context.archetype_tool.lookupObject(skw))
  context.setCategories(val)
  return state.set(portal_status_message='content categorized with keyword %s.' % SearchKW)

if sel_button:
    if kw is not None:
        storage = context.portal_classification.getStorage()
        
        #keyword = getattr(storage, kw)
        #newUID = keyword #.UID()
        
        val = context.getCategories()
        #k=context.archetype_tool.lookupObject(kw)
        #keywords.extend(k.getId())
        val.extend([kw])
        context.setCategories(val)
        #print "w"
        return state.set(portal_status_message='Selected keywords added.')
    else:
        #print "nw"
        return state.set(portal_status_message='No keywords selected.')

if sel2_button:
        kwA = context.archetype_tool.lookupObject(keyworda)
        if kwA.meta_type == "KeywordProposal":
            nameA = kwA.generateName(kwA.getKPTitle(), kwA.getShortAdditionalDescription())
        else:
            nameA = kwA.getName()
        context.setSearchKWA(nameA)
        return state.set(portal_status_message='Selected keyword added.')

if sel3_button:
        kwB = context.archetype_tool.lookupObject(keywordb)
        if kwB.meta_type == "KeywordProposal":
            nameB = kwB.generateName(kwB.getKPTitle(), kwB.getShortAdditionalDescription())
        else:
            nameB = kwB.getName()
        context.setSearchKWB(nameB)
        return state.set(portal_status_message='Selected keyword added.')

if se3_button: 
        return state.set()

if se4_button:
        context.setSearchKWA(SearchKWA)
        return state.set()

if se5_button:
        context.setSearchKWB(SearchKWB)
        return state.set()

if del_button:
    archetype_tool = context.archetype_tool

    if delKeywords is not None:
        storage = context.portal_classification.getStorage()
    
        keywords = [getattr(storage, kw) for kw in delKeywords]
    
        uids = context.getCategories() or []
 
        #obs = [archetype_tool.getObject(x) for x in uids]

        obs = [x.UID() for x in uids if x.getId() not in delKeywords]
        
        context.setCategories(obs)

        return state.set(portal_status_message='Selected keywords removed.')
    else:
        return state.set(portal_status_message='No keywords selected.')
