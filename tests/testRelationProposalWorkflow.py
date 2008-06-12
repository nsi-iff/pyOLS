import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from producttest import PloneOntologyTestCase

class TestRelationProposalWF(PloneOntologyTestCase):
    '''Test the RelationProposal Workflow'''

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.ct = self.portal.portal_classification
        self.wf = self.portal.portal_workflow
        self.ct.addKeyword("Bar")
        self.ct.addKeyword("Foo")
        test_ruleset = self.ct.addRelation('testOf')
        self.folder.invokeFactory('RelationProposal', id='rp')
        prop=getattr(self.folder, 'rp')
        self.portal.portal_catalog.reindexObject(prop, )
        kwa=self.ct.searchMatchingKeywordsFor(object, search="Bar", search_kw_proposals='false', search_linked_keywords='true')[0].getName()
        kwb=self.ct.searchMatchingKeywordsFor(object, search="Foo", search_kw_proposals='false', search_linked_keywords='true')[0].getName()
        prop.setRelation(prop.definedRelations()[0])
        prop.setSearchKWA(kwa)
        prop.setSearchKWB(kwb)

    def testRelationProposalWF(self):
        prop=getattr(self.folder, 'rp')
        wf_id="relation_proposal_workflow"
        self.wf.doActionFor(prop, 'submit', wf_id, )
        self.assertEqual(self.wf.getHistoryOf(wf_id, prop)[-1]['review_state'], 'pending')
        #test if we don't have Relationships yet:
        self.assertEqual(len(self.portal.portal_catalog.searchResults(portal_type='Keyword')[0].getObject().getRelations()), 0)
        print "RelationProposal submitted"
        self.wf.doActionFor(prop, 'reject', wf_id, )
        self.assertEqual(self.wf.getHistoryOf(wf_id, prop)[-1]['review_state'], 'private')
        print "RelationProposal rejected"
        self.wf.doActionFor(prop, 'submit', wf_id, )
        self.assertEqual(self.wf.getHistoryOf(wf_id, prop)[-1]['review_state'], 'pending')
        print "RelationProposal submitted again"
        self.wf.doActionFor(prop, 'approve', wf_id, )
        self.assertEqual(self.wf.getHistoryOf(wf_id, prop)[-1]['review_state'], 'approved')
        print "RelationProposal approved"
        #test if we do have Relationships now, after going through the workflow:
        self.assertEqual(self.portal.portal_catalog.searchResults(portal_type='Keyword')[0].getObject().getRelations()[0], 'testOf')
        self.assertEqual(self.portal.portal_catalog.searchResults(portal_type='Keyword')[1].getObject().getBackRelations()[0], 'testOf')
        self.assertEqual(self.portal.portal_catalog.searchResults(portal_type='Keyword')[0].getObject().getReferences()[0], self.portal.portal_catalog.searchResults(portal_type='Keyword')[1].getObject())

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    tests = TestRelationProposalWF,
    for test in tests:
        suite.addTest(makeSuite(test))
    return suite

if __name__ == '__main__':
    framework()
