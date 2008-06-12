from Products.CMFPlone.LargePloneFolder import LargePloneFolder
from Products.Archetypes.atapi import BaseBTreeFolderSchema, BaseBTreeFolder, registerType

class ProposalArchive(BaseBTreeFolder):
    """Archive of accepted keyword proposals.
    """
    schema = BaseBTreeFolderSchema
    filter_content_types = True
    allowed_content_types = ('KeywordProposal', 'RelationProposal')
    global_allow = False

registerType(ProposalArchive)
