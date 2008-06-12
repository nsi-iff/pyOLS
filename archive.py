from Products.CMFPlone.LargePloneFolder import LargePloneFolder
from Products.Archetypes.atapi import BaseBTreeFolderSchema, BaseBTreeFolder, registerType
from AccessControl.SecurityInfo import ClassSecurityInfo

class ProposalArchive(BaseBTreeFolder):
    """Archive of accepted keyword proposals.
    """
    schema = BaseBTreeFolderSchema
    filter_content_types = True
    allowed_content_types = ('KeywordProposal', 'RelationProposal')
    content_icon = "proposal_archive.gif"
    global_allow = False
    security = ClassSecurityInfo()
    security.declareObjectProtected("Manage Site")
    _properties = ({'id':'exclude_from_nav',
                    'type':'boolean',
                    'mode':'wd',
                    },)

registerType(ProposalArchive)
