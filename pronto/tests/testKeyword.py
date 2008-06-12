# -*- coding: utf-8 -*-
import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from producttest import PloneOntologyTestCase

class TestKeyword(PloneOntologyTestCase):
    """Test the keyword module.
    """

    def afterSetUp(self):
        self.setRoles(['Manager'])

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
        self.folder.invokeFactory('Document', id='child1Document')
        self.folder.invokeFactory('Document', id='child2Document')
        self.folder.child1Document.addReference(self.child, self.ctool.getClassifyRelationship())
        self.folder.child2Document.addReference(self.child, self.ctool.getClassifyRelationship())


    ###### The tests ##########

    def testGetReferences(self):
        self.assertEqual(self.father.getReferences('marriedWith'), [self.mother])
        self.assertEqual(self.mother.getReferences('parentOf'),    [self.child])
        self.assertEqual(self.child.getReferences('childOf'),      [self.father, self.mother])

    def testGetReferencesAllButClassifyRelationship(self):
        self.assertEqual(self.child.getReferences(), [self.father, self.mother])
        self.assertEqual(self.child.getRefs()      , [self.father, self.mother])

    def testGetBackReferences(self):
        self.assertEqual(self.father.getBackReferences('marriedWith'), [self.mother])
        self.assertEqual(self.mother.getBackReferences('childOf'),     [self.child])
        self.assertEqual(self.child.getBackReferences('parentOf'),     [self.father, self.mother])

    def testGetBackReferencesAllButClassifyRelationship(self):
        self.assertEqual(self.child.getBackReferences(), [self.father, self.mother])
        self.assertEqual(self.child.getBRefs()         , [self.father, self.mother, self.folder.child1Document, self.folder.child2Document])

    def testGetRelations(self):
        father_relations = self.father.getRelations()
        father_relations.sort()
        mother_relations = self.mother.getRelations()
        mother_relations.sort()
        child_relations = self.child.getRelations()
        child_relations_archetypes = self.child.getRelationships()
        child_relations.sort()
        child_relations_archetypes.sort()
        self.assertEqual(father_relations, ['marriedWith', 'parentOf'])
        self.assertEqual(mother_relations, ['marriedWith', 'parentOf'])
        self.assertEqual(child_relations,  ['childOf'])
        self.assertEqual(child_relations_archetypes, [self.ctool.getRelation(rel).getId() for rel in child_relations])

    def testGetBackRelations(self):
        father_backrelations = self.father.getBackRelations()
        father_backrelations.sort()
        mother_backrelations = self.mother.getBackRelations()
        mother_backrelations.sort()
        child_backrelations = self.child.getBackRelations()
        child_backrelations_archetypes = self.child.getBRelationships()
        child_backrelations_withClassifyRelation = [self.ctool.getRelation(rel).getId() for rel in child_backrelations] + [self.ctool.getClassifyRelationship()]
        child_backrelations.sort()
        child_backrelations_archetypes.sort()
        child_backrelations_withClassifyRelation.sort()
        self.assertEqual(father_backrelations, ['childOf', 'marriedWith'])
        self.assertEqual(mother_backrelations, ['childOf', 'marriedWith'])
        self.assertEqual(child_backrelations,  ['parentOf'])
        self.assertEqual(child_backrelations_archetypes, child_backrelations_withClassifyRelation)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestKeyword))
    return suite

if __name__ == '__main__':
    framework()