import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from producttest import PloneOntologyTestCase

class TestKeywordProposalWF(PloneOntologyTestCase):
    '''Test the KeywordProposal Workflow'''

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.ct = self.portal.portal_classification
        self.wf = self.portal.portal_workflow
        self.ct.addKeyword("Bar")
        test_ruleset = self.ct.addRelation('testOf')
        self.folder.invokeFactory('KeywordProposal', id='kwp')
        self.folder.kwp.setTitle('KWP')
        self.folder.kwp.setShortAdditionalDescription('shorty')
        self.folder.kwp.setKeywordProposalDescription('described it is')
        prop=getattr(self.folder, 'kwp')
        self.folder.kwp.invokeFactory('RelationProposal', id='rp')
        object=getattr(self.folder.kwp, 'rp')
        kwb=self.ct.searchMatchingKeywordsFor(object, search="Bar", search_kw_proposals='false', search_linked_keywords='true')[0].getName()
        object.setRelation(object.definedRelations()[0])
        object.setSearchKWB(kwb)
        prop.addReference(object, relationship='hasRelation', )

    def testKeywordProposalWF(self):
        prop=getattr(self.folder, 'kwp')
        wf_id="keyword_proposal_workflow"
        self.wf.doActionFor(prop, 'submit', wf_id, )
        self.assertEqual(self.wf.getHistoryOf(wf_id, prop)[-1]['review_state'], 'pending')
        print "KeywordProposal submitted"
        self.wf.doActionFor(prop, 'reject', wf_id, )
        self.assertEqual(self.wf.getHistoryOf(wf_id, prop)[-1]['review_state'], 'private')
        print "KeywordProposal rejected"
        self.wf.doActionFor(prop, 'submit', wf_id, )
        self.assertEqual(self.wf.getHistoryOf(wf_id, prop)[-1]['review_state'], 'pending')
        print "KeywordProposal submitted again"
        self.wf.doActionFor(prop, 'approve', wf_id, )
        self.assertEqual(self.wf.getHistoryOf(wf_id, prop)[-1]['review_state'], 'approved')
        print "KeywordProposal approved"
        self.assertEqual(self.portal.portal_catalog.searchResults(portal_type='Keyword')[0].getObject().getBackReferences()[0], self.portal.portal_catalog.searchResults(portal_type='Keyword')[1].getObject())

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    tests = TestKeywordProposalWF,
    for test in tests:
        suite.addTest(makeSuite(test))
    return suite

if __name__ == '__main__':
    framework()