## Script (Python) "upgradeNames"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=
##

""" Migration script for upgrading old relation and keyword ids to new names and titles and renaming the classification AT reference to the current value. """

from Products.PloneOntology.utils import generateUniqueId
from Products.PloneOntology.owl   import isXMLNCName, toXMLNCName

import logging
import re

logger = logging.getLogger('Products.PloneOntology.scripts.upgradeNames')

logger.info("Upgrade started.")

catalog = context.portal_catalog
ctool   = context.portal_classification

# find all relation rulesets.
relations = [result.getObject() for result in catalog.searchResults(portal_type="Ruleset")]

# filter rulesets with generated ids and XML NCNames.
relations = [relation for relation in relations if (not re.match('ruleset\.\d{4}-\d{2}-\d{2}\.\d{10}', relation.getId()))
                                                or (not isXMLNCName(relation.Title()))]


logger.info('Upgrade needed for %d relations.' % len(relations))
upgradedRelations = 0
skippedRelations  = 0
for relation in relations:
    logger.info("Upgrade relation %s" % relation)
    # save old title as beginning of description.
    oldTitle       = relation.Title()
    oldDescription = relation.Description()
    if oldTitle:
        newDescription = oldTitle
        if oldDescription:
            newDescription += "\n\n" + oldDescription

    # make new title from id.
    newTitle = relation.getId()
    if not isXMLNCName(newTitle):
        newTitle = toXMLNCName(newTitle)
        logger.info("Relation name has been xmlified to '%s'." % newTitle)
    used = ctool.isUsedName(newTitle, type="Ruleset")
    if used:
        logger.warn("Relation name '%s' is already used by '%s'! Skipping relation '%s'." % (newTitle, used, relation.getId()))
        skippedRelations += 1
        continue
    newId = generateUniqueId('Ruleset')

    relation.setTitle(newTitle)
    relation.setDescription(newDescription)
    relation.setId(newId)
    relation.reindexObject()
    logger.info("ID for relation '%s' changed to generated '%s'." % (relation.Title(), relation.getId()))
    upgradedRelations += 1

# find all keywords.
keywords = [result.getObject() for result in catalog.searchResults(portal_type="Keyword")]

# filter keywords with generated ids and XML NCNames.
keywords = [keyword for keyword in keywords if (not re.match('keyword\.\d{4}-\d{2}-\d{2}\.\d{10}', keyword.getId()))
                                            or (not isXMLNCName(keyword.getName()))]

logger.info('Upgrade needed for %d keywords.' % len(keywords))
upgradedKeywords = 0
skippedKeywords  = 0
for keyword in keywords:
    logger.info('Upgrade keyword %s' % keyword)
    newName = keyword.getId()
    if not isXMLNCName(newName):
        newName = toXMLNCName(newName)
        logger.info("Keyword name has been xmlified to '%s'." % newName)
    used = ctool.isUsedName(newName, type="Keyword")
    if used:
        logger.warn("Keyword name '%s' is already used by '%s'! Skipping keyword '%s'." % (newName, used, keyword.getId()))
        continue
        skippedKeywords += 1
    newId = generateUniqueId('Keyword')

    keyword.setName(newName)
    if not keyword.Title():
        keyword.setTitle(newName)
    try:
        oldShortDescription = keyword.short_additional_description
        # FIXME This yields a TypeError (attribute-less object): del keyword.short_additional_description
        if oldShortDescription:
            keyword.setShortAdditionalDescription(oldShortDescription)
    except AttributeError:
        pass
    keyword.setId(newId)
    keyword.unmarkCreationFlag()
    keyword.reindexObject()
    logger.info("ID for keyword '%s' changed to generated '%s'." % (keyword.getName(), keyword.getId()))
    upgradedKeywords += 1

logger.info('Upgrade content classification reference.')
ctool.changeClassifyRelationship('classifiedAs', ctool.getClassifyRelationship())

logger.info("Upgrade finished.")

if upgradedRelations or skippedRelations or upgradedKeywords or skippedKeywords:
    return state.set(portal_status_message="Relations: %d upgraded, %d skipped; Keywords: %d upgraded, %d skipped." % (upgradedRelations, skippedRelations, upgradedKeywords, skippedKeywords))
else:
    return state.set(portal_status_message="Nothing needed to be upgraded.")
