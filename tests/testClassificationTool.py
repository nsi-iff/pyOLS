import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from types import *

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

from Products.Relations import interfaces
from Products.Relations.exception import ValidationException
from zExceptions import NotFound
import re

# Install necessary products to portal
ZopeTestCase.installProduct('Relations')
ZopeTestCase.installProduct('PloneOntology')

class TestClassificationTool(PloneTestCase.PloneTestCase):
    '''Test the NIP ClassificationTool application'''

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.qi = self.portal.portal_quickinstaller
        self.qi.installProduct('Relations')
        self.qi.installProduct('PloneOntology')

        self.rtool = self.portal.relations_library
        self.ctool = self.portal.portal_classification
        self.storage = self.ctool.getStorage()

    ###### The tests ##########

    def testKeywordCreationDefault(self):
        kw = self.ctool.addKeyword('test')
        self.assertEqual(kw.title, '')
        self.assertEqual(kw.getKwDescription(), '')
        self.assertEqual(kw.short_additional_description, '')

    def testKeywordCreationParameter(self):
        kw = self.ctool.addKeyword('test', 'test_title', 'test_description', 'test_short_additional_description')
        self.assertEqual(kw.title, 'test_title')
        self.assertEqual(kw.getKwDescription(), 'test_description')
        self.assertEqual(kw.short_additional_description, 'test_short_additional_description')

    def testKeywordCreationAlreadyExisting(self):
        kw = self.ctool.addKeyword('test')

        self.failUnlessRaises(NameError, self.ctool.addKeyword, 'test')

    def testKeywordCreationEmptyName(self):
        self.failUnlessRaises(ValidationException, self.ctool.addKeyword, '')
        
    def testKeywordFetchExisting(self):
        kw = self.ctool.addKeyword('test')
        kw2 = self.ctool.getKeyword('test')

        self.assertEqual(kw, kw2)

    def testKeywordFetchNotExisting(self):
        self.failUnlessRaises(KeyError, self.ctool.getKeyword, 'test')

    def testKeywordDeleteExisting(self):
        kw = self.ctool.addKeyword('test')
        self.ctool.delKeyword('test')

        self.failIf(kw in self.ctool.keywords())

    def testKeywordDeleteNotExisting(self):
        self.ctool.delKeyword('test')
            
        try:
            kw = self.ctool.getKeyword('test')
            self.fail("Keyword 'test' shouldn't be there")
        except KeyError:
            pass

    def testRelationCreationDefault(self):
        test_ruleset = self.ctool.addRelation('testOf')

        self.assertAlmostEqual(0.0, test_ruleset.weight)
        self.failIf(hasattr(test_ruleset, 'transitive'))

        inverses = test_ruleset.getComponents(interfaces.IRule)
        self.assertEqual([], inverses)

    def testRelationCreationParameter(self):
        r1 = self.ctool.addRelation('testOf', 0.5, ['transitive', 'symmetric', 'functional', 'inversefunctional'], [])

        self.assertAlmostEqual(0.5, r1.weight)
        self.failUnless(r1.transitive)
        self.assertEqual(r1, r1.symmetric.getInverseRuleset())
        self.assertEqual(0 , r1.functional.getMinTargetCardinality())
        self.assertEqual(1, r1.functional.getMaxTargetCardinality())
        self.assertEqual(0, r1.inversefunctional.getMinSourceCardinality())
        self.assertEqual(1, r1.inversefunctional.getMaxSourceCardinality())

    def testRelationCreationInverseExisting(self):
        r2 = self.ctool.addRelation('testOf2')
        r1 = self.ctool.addRelation('testOf', inverses=['testOf2'])

        self.assertEqual(r2, r1.inverseOf_testOf2.getInverseRuleset())
        self.assertEqual(r1, r2.inverseOf_testOf.getInverseRuleset())

    def testRelationCreationInverseNotExisting(self):
        r1 = self.ctool.addRelation('testOf', inverses=['testOf2'])

        try:
            r2 = self.ctool.getRelation('testOf2')
        except KeyError:
            self.fail("Necessary relation not created.")

        self.assertEqual(r2, r1.inverseOf_testOf2.getInverseRuleset())
        self.assertEqual(r1, r2.inverseOf_testOf.getInverseRuleset())

    def testRelationFetchExisting(self):
        r1 = self.ctool.addRelation('testOf')
        r2 = self.ctool.getRelation('testOf')
        self.assertEqual(r1, r2)

    def testRelationFetchNotExisting(self):
        self.failUnlessRaises(KeyError, self.ctool.getRelation, 'testOf')

    def testRelationListing(self):
        r1 = self.ctool.addRelation('testOf')
        r2 = self.ctool.addRelation('testOf2')
        r3 = self.ctool.addRelation('testOf3')

        l = self.ctool.relations(self.rtool)
        self.assert_('testOf' in l)
        self.assert_('testOf2' in l)
        self.assert_('testOf3' in l)

    def testRelationDeleteExisting(self):
        r1 = self.ctool.addRelation('testOf')
        r2 = self.ctool.addRelation('testOf2')
        r3 = self.ctool.addRelation('testOf3')

        self.ctool.delRelation('testOf3')
        l = self.ctool.relations(self.rtool)
        self.failIf('testOf3' in l)

    def testRelationDeleteNotExisting(self):
        try:
            self.ctool.delRelation('testOf3')
        except AttributeError, KeyError:
            self.fail("Uncatched exception")
            
        l = self.ctool.relations(self.rtool)
        self.failIf('testOf3' in l)
        
    def testRelationSetWeightNotExisting(self):
        self.assertRaises(KeyError, self.ctool.setWeight, 'unrelatedTo', 0.7)

    def testRelationSetWeight(self):
        r1 = self.ctool.addRelation('testOf')
        self.ctool.setWeight('testOf', 0.5)
        self.assertAlmostEqual(0.5, self.ctool.getWeight('testOf'))

    def testRelationSetWeightExternalRelation(self):
        self.rtool.invokeFactory("Ruleset", 'relatedTo')
        r1 = self.ctool.getRelation('relatedTo')

        self.ctool.setWeight('relatedTo', 0.7)
        self.assertAlmostEqual(0.7, self.ctool.getWeight('relatedTo'))

    def testRelationGetWeightExternalRelation(self):
        self.rtool.invokeFactory("Ruleset", 'relatedTo')
        r1 = self.ctool.getRelation('relatedTo')

        self.assertAlmostEqual(0.0, self.ctool.getWeight('relatedTo'))

    def testRelationSetWeightNegative(self):
        r1 = self.ctool.addRelation('testOf')
        self.ctool.setWeight('testOf', 0.5)
        self.ctool.setWeight('testOf', -2.5)
        self.assertAlmostEqual(0.5, self.ctool.getWeight('testOf'))
        
    def testRelationSetTypesNotExisting(self):
        self.assertRaises(KeyError, self.ctool.setTypes, 'unrelatedTo', [])
        
    def testRelationSetTypes(self):
        r1 = self.ctool.addRelation('testOf')
        self.ctool.setTypes('testOf', ['symmetric', 'functional', 'inversefunctional'])

        self.assertEqual(r1, r1.symmetric.getInverseRuleset())
        self.assertEqual(0, r1.functional.getMinTargetCardinality())
        self.assertEqual(1, r1.functional.getMaxTargetCardinality())
        self.assertEqual(0, r1.inversefunctional.getMinSourceCardinality())
        self.assertEqual(1, r1.inversefunctional.getMaxSourceCardinality())

        self.assert_('functional' in self.ctool.getTypes('testOf'))
        self.assert_('inversefunctional' in self.ctool.getTypes('testOf'))
        self.assert_('symmetric' in self.ctool.getTypes('testOf'))
        self.failIf(hasattr(r1, 'transitive'))

    def testRelationSetTypesOverride(self):
        r1 = self.ctool.addRelation('testOf')
        self.ctool.setTypes('testOf', ['symmetric', 'functional', 'inversefunctional'])
        self.ctool.setTypes('testOf', ['transitive'])

        self.assert_(r1.transitive)
        self.failIf(hasattr(r1, 'symmetric'))
        self.failIf(hasattr(r1, 'functional'))
        self.failIf(hasattr(r1, 'inversefunctional'))

        self.assertEqual(['transitive'], self.ctool.getTypes('testOf'))

    def testRelationsSetTypesEmptyList(self):
        r1 = self.ctool.addRelation('testOf')
        self.ctool.setTypes('testOf', ['symmetric', 'functional', 'inversefunctional'])
        self.ctool.setTypes('testOf', [])

        self.failIf(hasattr(r1, 'transitive'))
        self.failIf(hasattr(r1, 'symmetric'))
        self.failIf(hasattr(r1, 'functional'))
        self.failIf(hasattr(r1, 'inversefunctional'))

        self.assertEqual([], self.ctool.getTypes('testOf'))

    def testRelationsSetTypesIgnoresUnknown(self):
        r1 = self.ctool.addRelation('testOf')
        self.ctool.setTypes('testOf', ['symmetric', 'functional', 'inversefunctional'])
        self.ctool.setTypes('testOf', ['transitive', 'unknown'])

        self.assert_(r1.transitive)
        self.failIf(hasattr(r1, 'symmetric'))
        self.failIf(hasattr(r1, 'functional'))
        self.failIf(hasattr(r1, 'inversefunctional'))

        self.assertEqual(['transitive'], self.ctool.getTypes('testOf'))

    def testRelationSetInversesNotExisting(self):
        self.assertRaises(KeyError, self.ctool.setInverses, 'unrelatedTo', [])

    def testRelationSetInversesEmpty(self):
        r1 = self.ctool.addRelation('childOf')
        self.ctool.setInverses('childOf', [])

        self.assertEqual([], self.ctool.getInverses('childOf'))

        rules = [rule for rule in r1.getComponents(interfaces.IRule) if re.match('inverseOf', rule.getId())]
        self.assertEqual([], rules)

    def testRelationSetInverseExisting(self):
        r1 = self.ctool.addRelation('childOf')
        r2 = self.ctool.addRelation('parentOf')

        self.ctool.setInverses('childOf', ['parentOf'])

        self.assertEqual(['parentOf'], self.ctool.getInverses('childOf'))
        self.assertEqual(['childOf'], self.ctool.getInverses('parentOf'))

    def testRelationSetInverseNotExisting(self):
        r1 = self.ctool.addRelation('childOf')

        self.ctool.setInverses('childOf', ['parentOf'])

        self.assertEqual(['parentOf'], self.ctool.getInverses('childOf'))
        self.assertEqual(['childOf'], self.ctool.getInverses('parentOf'))

    def testRelationSetInverseOverride(self):
        r1 = self.ctool.addRelation('childOf')
        self.ctool.setInverses('childOf', ['parentOf'])
        self.ctool.setInverses('childOf', ['motherOf'])

        self.assertEqual(['motherOf'], self.ctool.getInverses('childOf'))
        self.assertEqual([], self.ctool.getInverses('parentOf'))
        self.assertEqual(['childOf'], self.ctool.getInverses('motherOf'))

    def testRelationSetInverseTypesInferring(self):
        r1 = self.ctool.addRelation('childOf', types=['symmetric', 'transitive', 'inversefunctional', 'functional'])
        r2 = self.ctool.addRelation('parentOf')

        self.ctool.setInverses('childOf', ['parentOf'])

        self.assert_('transitive' in self.ctool.getTypes('parentOf'))
        self.assert_('symmetric' in self.ctool.getTypes('parentOf'))
        self.assert_('functional' in self.ctool.getTypes('parentOf'))
        self.assert_('inversefunctional' in self.ctool.getTypes('parentOf'))

    def testRelationSetInversesEmptyDeletes(self):
        r1 = self.ctool.addRelation('childOf')
        self.ctool.setInverses('childOf', ['parentOf'])
        self.ctool.setInverses('childOf', [])

        self.assertEqual([], self.ctool.getInverses('childOf'))

        rules = [rule for rule in r1.getComponents(interfaces.IRule) if re.match('inverseOf', rule.getId())]
        self.assertEqual([], rules)

    def testReferenceNotExistingKeyword(self):
        self.ctool.addRelation('childOf',   1.0, ['functional'])
        self.ctool.addRelation('parentOf',  1.0, ['inversefunctional'], ['childOf'])
        self.ctool.addRelation('synonymOf', 1.0, ['symmetric'])
        father = self.ctool.addKeyword('father')
        mother = self.ctool.addKeyword('mother')
        child  = self.ctool.addKeyword('child')

        self.ctool.addReference('child', 'kid', 'synonymOf')
        try:
            kid = self.ctool.getKeyword('kid')
        except KeyError:
            self.fail("Necessary keyword was not created")

    def testReferenceNotExistingRelation(self):
        father = self.ctool.addKeyword('father')
        child  = self.ctool.addKeyword('child')

        self.failUnlessRaises(NotFound, self.ctool.addReference,'father', 'kid', 'parentOf')
        
    def testReferenceSymmetric(self):
        self.ctool.addRelation('synonymOf', 1.0, ['symmetric'])
        child  = self.ctool.addKeyword('child')
        kid  = self.ctool.addKeyword('kid')

        self.ctool.addReference('child', 'kid', 'synonymOf')
        self.assertEqual(child.getRefs('synonymOf'), [kid])
        self.assertEqual(kid.getRefs('synonymOf'), [child])

    def testReferenceFunctional(self):
        self.ctool.addRelation('childOf',   1.0, ['functional'])
        self.ctool.addRelation('parentOf',  1.0, ['inversefunctional'], ['childOf'])
        father = self.ctool.addKeyword('father')
        father = self.ctool.addKeyword('man')
        child  = self.ctool.addKeyword('child')

        self.ctool.addReference('father', 'child', 'parentOf')
        self.assertRaises(ValidationException, self.ctool.addReference, 'child', 'man', 'childOf')

    def testReferenceInverseFunctional(self):
        self.ctool.addRelation('childOf',   1.0, ['functional'])
        self.ctool.addRelation('parentOf',  1.0, ['inversefunctional'], ['childOf'])
        father = self.ctool.addKeyword('father')
        man = self.ctool.addKeyword('man')
        child  = self.ctool.addKeyword('child')

        self.ctool.addReference('father', 'child', 'parentOf')
        self.assertRaises(ValidationException, self.ctool.addReference, 'man', 'child', 'parentOf')

    def testReferenceDeleteMaintainSymmetry(self):
        self.ctool.addRelation('synonymOf', 1.0, ['symmetric'])
        child  = self.ctool.addKeyword('child')
        kid  = self.ctool.addKeyword('kid')

        self.ctool.addReference('child', 'kid', 'synonymOf')
        self.ctool.delReference('kid', 'child', 'synonymOf')

        self.assertEqual(child.getRefs('synonymOf'), [])
        self.assertEqual(kid.getRefs('synonymOf'), [])

    def testReferenceDeleteMaintainSymmetryFunctional(self):
        self.ctool.addRelation('childOf',   1.0, ['functional'])
        self.ctool.addRelation('parentOf',  1.0, ['inversefunctional'], ['childOf'])
        father = self.ctool.addKeyword('father')
        child  = self.ctool.addKeyword('child')

        self.ctool.addReference('father', 'child', 'parentOf')
        self.ctool.delReference('child', 'father', 'childOf')

        self.assertEqual(child.getRefs('childOf'), [])
        self.assertEqual(father.getRefs('parentOf'), [])
        
    def testReferenceDeleteNotExistingNotCreated(self):
        self.ctool.addRelation('synonymOf', 1.0, ['symmetric'])
        child  = self.ctool.addKeyword('child')
        self.ctool.delReference('son', 'child', 'synonymOf')

        self.failIf('son' in self.ctool.keywords(), "Keyword created on reference delete")

    def testReferenceDeleteUnknownRelation(self):
        child  = self.ctool.addKeyword('child')
        kid  = self.ctool.addKeyword('kid')

        self.assertRaises(NotFound, self.ctool.delReference, 'child', 'kid', 'siblingOf')
        
    def testEmptyAfterCreation(self):
        """Tool contains no keywords after initialization"""
        self.assertEqual(len(self.ctool.objectIds('Keyword')), 0)

    def testKeywordCreation(self):
        """Creating keywords in object is possible"""
        self.ctool.manage_addKeyword("Thomas")
        self.assertEqual(len(self.storage.objectIds('Keyword')), 1)

    def testSearchOnEmptyStorage(self):
        """
        No error if no keywords defined
        """
        result = self.ctool.search("Animal", "all")
        self.assertEqual(result, [])

    def testSettingSearchCutoff(self):
        self.ctool.setSearchCutoff(3)
        self.assertAlmostEqual(self.ctool.getSearchCutoff(), 3)

        self.ctool.setSearchCutoff(0.7)
        self.assertAlmostEqual(self.ctool.getSearchCutoff(), 0.7)

        self.ctool.setSearchCutoff('0.7')
        self.assertAlmostEqual(self.ctool.getSearchCutoff(), 0.7)

        self.failUnlessRaises(ValueError, self.ctool.setSearchCutoff, 'foo')

        self.ctool.setSearchCutoff(-0.7)
        self.assertAlmostEqual(self.ctool.getSearchCutoff(), 0)

        self.ctool.setSearchCutoff('-0.7')
        self.assertAlmostEqual(self.ctool.getSearchCutoff(), 0)

    def testRegisterNewKeywordRelation(self):
        self.ctool.addRelation('fooble', weight=0.5)

        self.failUnless('fooble' in self.ctool.relations(self.rtool))
        self.assertAlmostEqual(self.ctool.getWeight('fooble'), 0.5)

    def testRemoveKeywordRelation(self):
        self.ctool.addRelation('fooble', weight=0.5)
        self.ctool.delRelation('fooble')

        self.failIf('fooble' in self.ctool.relations(self.rtool))

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(TestClassificationTool))
        return suite
