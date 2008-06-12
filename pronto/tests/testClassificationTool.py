# -*- coding: utf-8 -*-
import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from producttest import PloneOntologyTestCase

from Products.Relations import interfaces
from Products.Relations.exception import ValidationException
from Products.PloneOntology.utils import generateUniqueId

from zExceptions import NotFound
import re

class TestClassificationTool(PloneOntologyTestCase):
    """Test the ctool module.
    """

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.rtool = self.portal.relations_library
        self.ctool = self.portal.portal_classification
        self.storage = self.ctool.getStorage()

    ###### The tests ##########

    def testKeywordCreationDefault(self):
        kw = self.ctool.addKeyword('test')
        self.assertEqual(kw.title, 'test')
        self.assertEqual(kw.getKwDescription(), '')
        self.assertEqual(kw.shortAdditionalDescription, '')

    def testKeywordCreationParameter(self):
        kw = self.ctool.addKeyword('test', 'test_title', 'test_description', 'test_short_additional_description')
        self.assertEqual(kw.getName(), 'test')
        self.assertEqual(kw.title, 'test_title')
        self.assertEqual(kw.getKwDescription(), 'test_description')
        self.assertEqual(kw.shortAdditionalDescription, 'test_short_additional_description')

    def testKeywordCreationAlreadyExisting(self):
        kw = self.ctool.addKeyword('test')
        self.failUnlessRaises(NameError, self.ctool.addKeyword, 'test')

    def testKeywordCreationEmptyName(self):
        self.failUnlessRaises(ValidationException, self.ctool.addKeyword, '')

    def testKeywordCreationNonXMLName(self):
        self.failUnlessRaises(ValidationException, self.ctool.addKeyword, 'this is no xml name')

    def testKeywordCreationNonASCIIName(self):
        kw1 = self.ctool.addKeyword("äöüß")
        kw2 = self.ctool.getKeyword("äöüß")
        self.assertEqual(kw1, kw2)

    def testKeywordCreationFromExistingUID(self):
        self.storage.invokeFactory('Keyword', 'test_uid')
        kw = self.ctool.addKeyword('test', uid='test_uid')
        self.assertEqual(kw, getattr(self.storage, 'test_uid'))

    def testKeywordCreationFromNotExistingUID(self):
        self.failUnlessRaises(AttributeError, self.ctool.addKeyword, 'test', uid='no_such_uid')

    def testKeywordFetchExisting(self):
        kw = self.ctool.addKeyword('test')
        kw2 = self.ctool.getKeyword('test')

        self.assertEqual(kw, kw2)

    def testKeywordFetchNotExisting(self):
        self.failUnlessRaises(NotFound, self.ctool.getKeyword, 'test')

    def testKeywordFetchEmpty(self):
        self.ctool.addKeyword('nonempty')
        self.failUnlessRaises(ValidationException, self.ctool.getKeyword, '')

    def testKeywordUsedName(self):
        self.ctool.addKeyword('test')
        self.failUnless(self.ctool.isUsedName('test'))

    def testKeywordUsedNameObject(self):
        kw = self.ctool.addKeyword('test')
        self.assertEqual(kw, self.ctool.isUsedName('test'))

    def testKeywordUnusedName(self):
        self.ctool.addKeyword('test1')
        self.failIf(self.ctool.isUsedName('test2'))

    def testKeywordDeleteExisting(self):
        kw = self.ctool.addKeyword('test')
        self.ctool.delKeyword('test')

        self.failIf(kw in self.ctool.keywords())

    def testKeywordDeleteNotExisting(self):
        self.ctool.delKeyword('test')

        try:
            kw = self.ctool.getKeyword('test')
            self.fail("Keyword 'test' shouldn't be there")
        except NotFound:
            pass

    def testKeywordListing(self):
        k1 = self.ctool.addKeyword('test')
        k2 = self.ctool.addKeyword('test2')
        k3 = self.ctool.addKeyword('test3')
        k4 = self.ctool.addKeyword('äöüß')

        k = self.ctool.keywords()
        self.assertEqual(k, ['test', 'test2', 'test3', 'äöüß'])

    def testKeywordRenameFetchNew(self):
        kw = self.ctool.addKeyword('test1')
        kw.setName('test2')
        kw.reindexObject()
        self.assertEqual(kw, self.ctool.getKeyword('test2'))

    def testKeywordRenameFetchOld(self):
        kw = self.ctool.addKeyword('test1')
        kw.setName('test2')
        kw.reindexObject()
        self.failUnlessRaises(NotFound, self.ctool.getKeyword, 'test1')

    def testKeywordRenameListing(self):
        kw = self.ctool.addKeyword('test1')
        kw.setName('test2')
        self.assertEqual(['test2'], self.ctool.keywords())

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

        self.assertEqual(r2, getattr(r1, 'inverseOf_' + r2.getId()).getInverseRuleset())
        self.assertEqual(r1, getattr(r2, 'inverseOf_' + r1.getId()).getInverseRuleset())

    def testRelationCreationInverseNotExisting(self):
        r1 = self.ctool.addRelation('testOf', inverses=['testOf2'])

        try:
            r2 = self.ctool.getRelation('testOf2')
        except NotFound:
            self.fail("Necessary relation not created.")

        self.assertEqual(r2, getattr(r1, 'inverseOf_' + r2.getId()).getInverseRuleset())
        self.assertEqual(r1, getattr(r2, 'inverseOf_' + r1.getId()).getInverseRuleset())

    def testRelationFetchExisting(self):
        r1 = self.ctool.addRelation('testOf')
        r2 = self.ctool.getRelation('testOf')
        self.assertEqual(r1, r2)

    def testRelationFetchNotExisting(self):
        self.failUnlessRaises(NotFound, self.ctool.getRelation, 'testOf')

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
        self.assertRaises(NotFound, self.ctool.setWeight, 'unrelatedTo', 0.7)

    def testRelationSetWeight(self):
        r1 = self.ctool.addRelation('testOf')
        self.ctool.setWeight('testOf', 0.5)
        self.assertAlmostEqual(0.5, self.ctool.getWeight('testOf'))

    def testRelationSetWeightExternalRelation(self):
        self.rtool.invokeFactory("Ruleset", generateUniqueId('Ruleset'), title='relatedTo')
        r1 = self.ctool.getRelation('relatedTo')

        self.ctool.setWeight('relatedTo', 0.7)
        self.assertAlmostEqual(0.7, self.ctool.getWeight('relatedTo'))

    def testRelationGetWeightExternalRelation(self):
        self.rtool.invokeFactory("Ruleset", generateUniqueId('Ruleset'), title='relatedTo')
        r1 = self.ctool.getRelation('relatedTo')

        self.assertAlmostEqual(0.0, self.ctool.getWeight('relatedTo'))

    def testRelationSetWeightNegative(self):
        r1 = self.ctool.addRelation('testOf')
        self.ctool.setWeight('testOf', 0.5)
        self.ctool.setWeight('testOf', -2.5)
        self.assertAlmostEqual(0.5, self.ctool.getWeight('testOf'))

    def testRelationSetTypesNotExisting(self):
        self.assertRaises(NotFound, self.ctool.setTypes, 'unrelatedTo', [])

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
        self.assertRaises(NotFound, self.ctool.setInverses, 'unrelatedTo', [])

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
        except NotFound:
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
        self.assertEqual(child.getReferences('synonymOf'), [kid])
        self.assertEqual(kid.getReferences('synonymOf'), [child])

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

        self.assertEqual(child.getReferences('synonymOf'), [])
        self.assertEqual(kid.getReferences('synonymOf'), [])

    def testReferenceDeleteMaintainSymmetryFunctional(self):
        self.ctool.addRelation('childOf',   1.0, ['functional'])
        self.ctool.addRelation('parentOf',  1.0, ['inversefunctional'], ['childOf'])
        father = self.ctool.addKeyword('father')
        child  = self.ctool.addKeyword('child')

        self.ctool.addReference('father', 'child', 'parentOf')
        self.ctool.delReference('child', 'father', 'childOf')

        self.assertEqual(child.getReferences('childOf'), [])
        self.assertEqual(father.getReferences('parentOf'), [])

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

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestClassificationTool))
    return suite

if __name__ == '__main__':
    framework()
