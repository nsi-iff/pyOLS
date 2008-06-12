## Script (Python) "set_relevance_factors"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=factors={}
##title=
##

ctool = context.portal_classification
for r in factors.keys():
    ctool.setWeight(r, float(factors[r]))
return state.set(portal_status_message='Relevance factors changed.')

