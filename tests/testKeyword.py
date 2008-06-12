# -*- coding: utf-8 -*-
import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from types import *

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

from Products.Relations import interfaces
from Products.Relations.exception import ValidationException
import Products.Relations

# Install necessary products to portal
ZopeTestCase.installProduct('Relations')
ZopeTestCase.installProduct('PloneOntology')

class TestKeyword(PloneTestCase.PloneTestCase):
    """Test the NIP ClassificationTool application.
    """

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.qi = self.portal.portal_quickinstaller
        self.qi.installProduct('Relations')
        self.qi.installProduct('PloneOntology')

        self.rtool = self.portal.relations_library
        self.ctool = self.portal.portal_classification
        self.storage = self.ctool.getStorage()

        self.father = self.ctool.addKeyword('father')
        self.mother = self.ctool.addKeyword('mother')
        self.child = self.ctool.addKeyword('child')
        self.ctool.addRelation('childOf'  , 1.0, ['transitive'], ['parentOf'])
        self.ctool.addRelation('marriedWith', 1.0, ['symmetric'])
        self.ctool.addReference('father', 'mother', 'marriedWith')
        self.ctool.addReference('father', 'child', 'parentOf')
        self.ctool.addReference('mother', 'child', 'parentOf')


    ###### The tests ##########

    def testGetReferences(self):
        self.assertEqual(self.father.getReferences('marriedWith'), [self.mother])
        self.assertEqual(self.mother.getReferences('parentOf'),    [self.child])
        self.assertEqual(self.child.getReferences('childOf'),      [self.father, self.mother])

    def testGetBackReferences(self):
        self.assertEqual(self.father.getBackReferences('marriedWith'), [self.mother])
        self.assertEqual(self.mother.getBackReferences('childOf'),     [self.child])
        self.assertEqual(self.child.getBackReferences('parentOf'),     [self.father, self.mother])

    def testGetRelations(self):
        father_relations = self.father.getRelations()
        father_relations.sort()
        mother_relations = self.mother.getRelations()
        mother_relations.sort()
        child_relations = self.child.getRelations()
        child_relations.sort()
        self.assertEqual(father_relations, ['marriedWith', 'parentOf'])
        self.assertEqual(mother_relations, ['marriedWith', 'parentOf'])
        self.assertEqual(child_relations,  ['childOf'])

    def testGetBackRelations(self):
        father_backrelations = self.father.getBackRelations()
        father_backrelations.sort()
        mother_backrelations = self.mother.getBackRelations()
        mother_backrelations.sort()
        child_backrelations = self.child.getBackRelations()
        child_backrelations.sort()
        self.assertEqual(father_backrelations, ['childOf', 'marriedWith'])
        self.assertEqual(mother_backrelations, ['childOf', 'marriedWith'])
        self.assertEqual(child_backrelations,  ['parentOf'])

if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(TestKeyword))
        return suite
