import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from producttest import PloneOntologyTestCase

class TestProduct(PloneOntologyTestCase):
    '''Test the PloneOntology ClassificationTool application'''

    def classify(self, obj, keyword):
        newUID = keyword.UID()

        keywords = obj.getRefs(self.ctool.getClassifyRelationship())
        if keyword not in keywords:
            obj.addReference(keyword, self.ctool.getClassifyRelationship())

        #val = obj.getCategories()
        #val.append(newUID)
        #obj.setCategories(val)

    def afterSetUp(self):
        self.setRoles(['Manager'])

        self.portal.acl_users._doAddUser('member', 'secret',
                                         ['Member'], [])
        self.portal.acl_users._doAddUser('reviewer', 'secret',
                                         ['Reviewer'], [])
        self.portal.acl_users._doAddUser('manager', 'secret',
                                         ['Manager'], [])

        self.ctool = self.portal.portal_classification
        self.rtool = self.portal.relations_library
        self.storage = self.ctool.getStorage()

        #create playground from empty ontology
        for k in self.ctool.keywords():
            self.ctool.delKeyword(k)
        for r in self.ctool.relations(self.rtool):
            self.ctool.delRelation(r)
        self.ctool.addRelation('parentOf', 0.5)
        self.ctool.addRelation('relatedTo', 0.7)

        self.kws = ["Mammal", "Vertebrate", "Animal",
               "Hair", "Bone", "Structure"]

        self.docs = ["A","B","C","D","E","F","G","H"]

        self.obs = {}
        for kw in self.kws:
            keyword = self.ctool.addKeyword(kw)
            self.obs[kw] = getattr(self.storage, keyword.getId())

        self.ctool.addReference("Vertebrate", "Mammal"    , 'parentOf')
        self.ctool.addReference("Animal"    , "Vertebrate", 'parentOf')
        self.ctool.addReference("Structure" , "Bone"      , 'parentOf')
        self.ctool.addReference("Structure" , "Hair"      , 'parentOf')

        self.ctool.addReference("Mammal", "Hair"  , 'relatedTo')
        self.ctool.addReference("Hair"  , "Mammal", 'relatedTo')

        self.ctool.addReference("Bone"      , "Vertebrate", 'relatedTo')
        self.ctool.addReference("Vertebrate", "Bone"      , 'relatedTo')

        #content (must support IReferenceable)
        for doc in self.docs:
            self.folder.invokeFactory('Document', id=doc)
            self.obs[doc] = getattr(self.folder, doc)

        #classification
        self.ctool.setClassifyRelationship('classifiedAs_byPloneOntologyTestProduct')
        self.classify(self.obs["A"],self.obs["Mammal"])
        self.classify(self.obs["A"],self.obs["Hair"])
        self.classify(self.obs["B"],self.obs["Mammal"])
        self.classify(self.obs["C"],self.obs["Vertebrate"])
        self.classify(self.obs["D"],self.obs["Hair"])
        self.classify(self.obs["E"],self.obs["Bone"])
        self.classify(self.obs["F"],self.obs["Mammal"])
        self.classify(self.obs["F"],self.obs["Bone"])

   ###### The tests ##########

    def testSkinInstallation(self):
        st = self.portal.portal_skins

        self.failUnless('PloneOntology' in st.objectIds())

    def testPreserveKeywordsOnReinstall(self):
        self.portal.portal_quickinstaller.uninstallProducts(['PloneOntology'])

        self.failUnless('kw_storage' in self.portal.objectIds())
        storage = self.portal.kw_storage

        for kw in self.kws:
            self.failUnless(self.obs[kw].getId() in storage.objectIds())
            self.failUnlessEqual(self.obs[kw], getattr(storage, self.obs[kw].getId()))

        self.portal.portal_quickinstaller.installProduct('PloneOntology')

        storage = self.portal.kw_storage

        for kw in self.kws:
            self.failUnless(self.obs[kw].getId() in storage.objectIds())
            self.failUnlessEqual(self.obs[kw], getattr(storage, self.obs[kw].getId()))

    def testStrictSearch(self):
        """
        Only directly classified content
        """
        result = self.ctool.search("Animal", links=[])
        self.assertEqual(len(result), 0)

        result = self.ctool.search("Vertebrate", links=[])
        self.assertEqual(len(result), 1)

        result = self.ctool.search("Mammal", links=[])
        self.assertEqual(len(result), 3)

    def testRestrictedFullSearch(self):
        """
        Search in branch of keyword hierarchy --> only parentOf relations
        """
        result = self.ctool.search("Animal", ['parentOf'])
        self.assertEqual(len(result), 4) #A,B,C,F

        result = self.ctool.search("Vertebrate", ['parentOf'])
        self.assertEqual(len(result), 4) #A,B,C,F

        result = self.ctool.search("Mammal", ['parentOf'])
        self.assertEqual(len(result), 3) #A,B,F

        # same but with coercion to list
        result = self.ctool.search("Vertebrate", 'parentOf')
        self.assertEqual(len(result), 4) #A,B,C,F

        result = self.ctool.search("Mammal", 'parentOf')
        self.assertEqual(len(result), 3) #A,B,F

    def testFullSearch(self):
        """
        Search following all relations
        """
        result = self.ctool.search("Animal", "all")
        self.assertEqual(len(result), 6)

        result = self.ctool.search("Vertebrate", "all")
        self.assertEqual(len(result), 6)

        result = self.ctool.search("Mammal", "all")
        self.assertEqual(len(result), 4)

    def testSearchForNonexistingKeyword(self):
        """
        Empty Result if searching for nonexisting keyword
        """
        result = self.ctool.search("SDFZWEF", "all")
        self.assertEqual(result, [])

    def testRelatedKeyword(self):
        kws = self.ctool.getRelatedKeywords("Animal", links="all")

        self.assertAlmostEqual(kws["Vertebrate"], 0.5)
        self.assertAlmostEqual(kws["Mammal"], 0.25)
        self.assertAlmostEqual(kws["Bone"], 0.35)
        self.assertAlmostEqual(kws["Hair"], 0.7*0.25)

    def testCustomizeRelevanceFactor(self):
        self.ctool.setWeight('parentOf', 0.9)
        self.ctool.setWeight('relatedTo', 0.7)

        kws = self.ctool.getRelatedKeywords("Animal", links="all")
        self.assertAlmostEqual(kws["Vertebrate"], 0.9)
        self.assertAlmostEqual(kws["Mammal"], 0.9*0.9)
        self.assertAlmostEqual(kws["Bone"], 0.7*0.9)
        self.assertAlmostEqual(kws["Hair"], 0.7*0.9*0.9)

    def testCustomizeRelevanceFactorWithMapping(self):
        self.ctool.setWeight('parentOf', 0.3)
        self.ctool.setWeight('relatedTo', 0.3)

        kws = self.ctool.getRelatedKeywords("Animal", links="all")

        self.assertAlmostEqual(kws["Vertebrate"], 0.3)
        # self.assertAlmostEqual(kws["Mammal"], 0.3*0.3) # score < 0.1
        # self.assertAlmostEqual(kws["Bone"], 0.3*0.3)
        # self.assertAlmostEqual(kws["Hair"], 0.3*0.3*0.3)

    def testRelevanceCountingAndSorting(self):
        result = self.ctool.search("Animal", "all")
        self.assertEqual(len(result), 6)

        # assert first element is 'F' with 0.6
        first = result[0]
        self.assertEqual(first[1], self.obs['F'])
        self.assertAlmostEqual(first[0], 0.6)

    def testSearchCutoff(self):
        self.ctool.setWeight('parentOf', 0.3)
        self.ctool.setWeight('relatedTo', 0.3)

        kws = self.ctool.getRelatedKeywords("Animal", links="all")

        self.assertEqual(len(kws), 2)
        self.assertAlmostEqual(kws["Vertebrate"], 0.3)

        kws = self.ctool.getRelatedKeywords("Animal", links="all", cutoff=0.01)
        self.assertEqual(len(kws), 5)
        self.assertAlmostEqual(kws["Vertebrate"], 0.3)
        self.assertAlmostEqual(kws["Mammal"], 0.3*0.3)
        self.assertAlmostEqual(kws["Bone"], 0.3*0.3)
        self.assertAlmostEqual(kws["Hair"], 0.3*0.3*0.3)

    def testSearchWithAdditionalRelation(self):
        self.ctool.addRelation('fooble',  0.5)
        self.ctool.setWeight('parentOf',  0.3)
        self.ctool.setWeight('relatedTo', 0.3)

        self.obs["Mammal"].addReference(self.obs["Hair"], 'fooble')
        self.obs["Hair"].addReference(self.obs["Mammal"], 'fooble')

        kws = self.ctool.getRelatedKeywords("Animal", links="all")

        self.assertAlmostEqual(kws["Vertebrate"], 0.3)
        # self.assertAlmostEqual(kws["Mammal"], 0.3*0.3) #score < 0.1
        #self.assertAlmostEqual(kws["Bone"], 0.3*0.3)
        #self.assertAlmostEqual(kws["Hair"], 0.3*0.3*0.3+0.3*0.3*0.5)

    def testContentSearchWithoutFuzzy(self):
        result = self.ctool.searchFor(self.obs['A'], links=[]) # B,D
        self.assertEqual(len(result), 3)

        result = self.ctool.searchFor(self.obs['C'], links=[]) # nothing
        self.assertEqual(len(result), 0)

    def testContentSearchWithFuzzy(self):
        result = self.ctool.searchFor(self.obs['A']) # B,D
        self.assertEqual(len(result), 3)

        result = self.ctool.searchFor(self.obs['C'])
        # A,B,D,E,F
        self.assertEqual(len(result), 5)

    def testContentSearchForNonReferenceableObject(self):
        self.folder.invokeFactory('Document', id='foo')
        foo = getattr(self.folder, 'foo')

        result = self.ctool.searchFor(foo, links='all')
        self.assertEqual(len(result), 0)

    def testGetKeywordRelations(self):
        rels = self.ctool.relations(self.rtool)
        self.assertEqual(len(rels), 2)

        self.ctool.addRelation('fooble', 0.5)

        rels = self.ctool.relations(self.rtool)
        self.assertEqual(len(rels), 3)

    def testBUGAdditionalRelationBreaksRelatedBox(self):
        self.ctool.addRelation('childOf', 0.5)

        for ob in self.storage.objectValues():
            children = ob.getReferences('parentOf')

            for child in children:
                child.addReference(ob, 'childOf')

        results = self.ctool.searchFor(self.obs['A'])

        self.failUnless(len(results)>0)

    def testBUGRelevancyFactorsAreStrings(self):
        #XXX is this test relevant anymore???
        for fac in self.ctool.relevance_factors.values():
            self.assertEquals(type(fac),FloatType)

        #change some
        self.ctool.setWeight('parentOf', 0.3)

        for fac in self.ctool.relevance_factors.values():
            self.failUnless(type(fac) == FloatType)

    def testKeywordLinkedKeywords(self):
        res = self.obs['Animal'].getLinkedKeywords()
        self.assertEqual(len(res), 1)

        res = self.obs['Animal'].getLinkedKeywords('parentOf')
        self.assertEqual(len(res), 1)

        res = self.obs['Animal'].getLinkedKeywords('relatedTo')
        self.assertEqual(len(res), 0)

        res = self.obs['Mammal'].getLinkedKeywords()
        self.assertEqual(len(res), 1)

        res = self.obs['Mammal'].getLinkedKeywords('parentOf')
        self.assertEqual(len(res), 0)

        res = self.obs['Mammal'].getLinkedKeywords('relatedTo')
        self.assertEqual(len(res), 1)

        res = self.obs['Vertebrate'].getLinkedKeywords()
        self.assertEqual(len(res), 2)

        res = self.obs['Vertebrate'].getLinkedKeywords('parentOf')
        self.assertEqual(len(res), 1)

        res = self.obs['Vertebrate'].getLinkedKeywords('relatedTo')
        self.assertEqual(len(res), 1)

    def testKeywordContentValues(self):
        mammal = self.ctool.getKeyword("Mammal")
        obs = mammal.classifiedContentValues()

        self.assertEqual(3, len(obs))
        self.assert_(self.obs["A"] in obs)

    def testKeywordContentIds(self):
        mammal = self.ctool.getKeyword("Mammal")
        ids = mammal.classifiedContentIds()

        self.assertEqual(3, len(ids))
        self.assert_("B" in ids)

    def testKeywordContentItems(self):
        mammal = self.ctool.getKeyword("Mammal")
        items = mammal.classifiedContentItems()

        self.assertEqual(3, len(items))
        self.assert_(("F", self.obs["F"]) in items)

    def testKeywordFindDependent(self):
        v = self.ctool.getKeyword("Vertebrate")

        kws = v.findDependent(0)
        self.assertEqual([v], kws)

        kws = v.findDependent(1)
        self.assertEqual(3, len(kws))
        self.assert_(self.obs["Mammal"] in kws)
        self.failIf(self.obs["Hair"] in kws)

        kws = v.findDependent(2)
        self.assertEqual(4, len(kws))
        self.assert_(self.obs["Hair"] in kws)

    def testKeywordFindDependentExact(self):
        v = self.ctool.getKeyword("Vertebrate")

        kws = v.findDependent(0, exact=True)
        self.assertEqual([v], kws)

        kws = v.findDependent(1, exact=True)
        self.assertEqual(2, len(kws))
        self.assert_(self.obs["Mammal"] in kws)
        self.failIf(self.obs["Hair"] in kws)
        self.failIf(self.obs["Vertebrate"] in kws)

        kws = v.findDependent(2, exact=True)
        self.assertEqual([self.obs["Hair"]], kws)

        kws = v.findDependent(3, exact=True)
        self.assertEqual([], kws)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestProduct))
    return suite

if __name__ == '__main__':
    framework()