## Script (Python) "set_relevance_factors"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=factors={}, transitive={}, symmetric={}, functional={}, inversefunctional={}, inverseOf={}, relations
##title=
##

ctool = context.portal_classification

for r in factors.keys():
    ctool.setWeight(r, float(factors[r]))

for r in ctool.relations(context.relations_library):
    typeslist=ctool.getTypes(r)
    
    if r not in transitive.keys():
     if 'transitive' in typeslist:
          typeslist.remove('transitive')
    else:
     if 'transitive' not in typeslist:
          typeslist.append('transitive')

    if r not in symmetric.keys():
     if 'symmetric' in typeslist:
          typeslist.remove('symmetric')
    else:
     if 'symmetric' not in typeslist:
          typeslist.append('symmetric')
          
    if r not in functional.keys():
     if 'functional' in typeslist:
          typeslist.remove('functional')
    else:
     if 'functional' not in typeslist:
          typeslist.append('functional')

    if r not in inversefunctional.keys():
     if 'inversefunctional' in typeslist:
          typeslist.remove('inversefunctional')
    else:
     if 'inversefunctional' not in typeslist:
          typeslist.append('inversefunctional')
    
    if r not in inverseOf.keys():
     ctool.setInverses(r, [])
    elif inverseOf[r] == 'deleteAll':
     ctool.setInverses(r, [])    
    elif inverseOf[r] != 'noChange':
     ctool.setInverses(r, [inverseOf[r]])
          
    ctool.setTypes(r, typeslist)
    
return state.set(portal_status_message='Relations changed.')

