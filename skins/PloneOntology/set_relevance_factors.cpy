## Script (Python) "set_relevance_factors"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=factors={}, transitive={}, relations
##title=
##

ctool = context.portal_classification
for r in factors.keys():
    ctool.setWeight(r, float(factors[r]))

for r in ctool.relations(context.relations_library):
    typeslist=ctool.getTypes(r)
    if r not in transitive.keys():
     typeslist=ctool.getTypes(r)
     if 'transitive' in typeslist:
          typeslist.remove('transitive')
    else:
     if 'transitive' not in typeslist:
          typeslist.append('transitive')
    ctool.setTypes(r, typeslist)
    
return state.set(portal_status_message='Relations changed.')

