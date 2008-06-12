import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from producttest import PloneOntologyTestCase

class TestRelationProposal(PloneOntologyTestCase):
    '''Test the RelationProposal Content Type'''

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.ct = self.portal.portal_classification
        foo = self.ct.addKeyword("Foo")
        bar = self.ct.addKeyword("Bar")
        test_ruleset = self.ct.addRelation('testOf')

    def testRelationProposalEdit(self):
        self.folder.invokeFactory('RelationProposal', id='rp')
        prop=getattr(self.folder, 'rp')
        dr=prop.definedRelations()
        self.folder.rp.setRelation(dr[0])
        self.assertEqual(self.folder.rp.getRelation(), dr[0])
        kwa=self.ct.searchMatchingKeywordsFor(prop, search="Foo", search_kw_proposals='false', search_linked_keywords='true')[0].getName()
        self.folder.rp.setSearchKWA(kwa)
        self.assertEqual(self.folder.rp.getSearchKWA(), kwa)
        kwb=self.ct.searchMatchingKeywordsFor(prop, search="Bar", search_kw_proposals='false', search_linked_keywords='true')[0].getName()
        self.folder.rp.setSearchKWB(kwb)
        self.assertEqual(self.folder.rp.getSearchKWB(), kwb)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    tests = TestRelationProposal,
    for test in tests:
        suite.addTest(makeSuite(test))
    return suite

if __name__ == '__main__':
    framework()