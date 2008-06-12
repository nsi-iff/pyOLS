import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from types import *

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase
from Products.Archetypes import Referenceable

from zExceptions import NotFound

# Install necessary products to portal
ZopeTestCase.installProduct('Relations')
ZopeTestCase.installProduct('PloneOntology')

class TestKeywordProposal(PloneTestCase.PloneTestCase):
    '''Test the KeywordProposal Content Type'''

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.qi = self.portal.portal_quickinstaller
        self.qi.installProduct('Relations')
        self.qi.installProduct('PloneOntology')
        self.ct = self.portal.portal_classification
        foo = self.ct.addKeyword("Foo")

    def testKeywordProposalEdit(self):
        self.folder.invokeFactory('KeywordProposal', id='kwp')
        self.folder.kwp.setShortAdditionalDescription('Foo')
        self.assertEqual(self.folder.kwp.getShortAdditionalDescription(), 'Foo')
        self.folder.kwp.setKeywordProposalDescription('described it is')
        self.assertEqual(self.folder.kwp.getKeywordProposalDescription(), 'described it is')
        prop=getattr(self.folder, 'kwp')
        self.folder.kwp.invokeFactory('RelationProposal', id='rp')
        object=getattr(self.folder.kwp, 'rp')
        kwb=self.ct.searchMatchingKeywordsFor(object, search="Foo", search_kw_proposals='false', search_linked_keywords='true')[0].getName()
        object.setSearchKWB(kwb)
        prop.addReference(object, relationship='hasRelation', )
        self.assertEqual(self.folder.kwp.getRelationProposals()[0].getId(), 'rp')

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    tests = TestKeywordProposal,
    for test in tests:
        suite.addTest(makeSuite(test))
    return suite

if __name__ == '__main__':
    framework()