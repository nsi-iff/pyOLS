import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

# Install necessary products to portal
ZopeTestCase.installProduct('Relations')
ZopeTestCase.installProduct('PloneOntology')

class TestProductInstallation(PloneTestCase.PloneTestCase):
    '''Test the NIP ClassificationTool application'''

    def classify(self, obj, keyword):
        newUID = keyword.UID()
        
        val = obj.getCategories()
        val.append(newUID)
        obj.setCategories(val)
        
    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.qi = self.portal.portal_quickinstaller
        self.qi.installProduct('Relations')
        self.qi.installProduct('PloneOntology')

        self.portal.acl_users._doAddUser('member', 'secret',
                                         ['Member'], [])
        self.portal.acl_users._doAddUser('reviewer', 'secret',
                                         ['Reviewer'], [])
        self.portal.acl_users._doAddUser('manager', 'secret',
                                         ['Manager'], [])
        
        self.ctool = self.portal.portal_classification
        self.storage = self.ctool.getStorage()
        
        #create playground
        kws = ["Mammal", "Vertebrate", "Animal",
               "Hair", "Bone", "Structure"]
        
        docs = ["A","B","C","D","E","F","G","H"]

        self.obs = {}
        for kw in kws:
            self.ctool.manage_addKeyword(kw)
            self.obs[kw] = getattr(self.storage, kw)

        self.obs["Vertebrate"].addReference(self.obs["Mammal"], 'parentOf')
        self.obs["Animal"].addReference(self.obs["Vertebrate"], 'parentOf')
        self.obs["Structure"].addReference(self.obs["Bone"], 'parentOf')
        self.obs["Structure"].addReference(self.obs["Hair"], 'parentOf')

        self.obs["Mammal"].addReference(self.obs["Hair"], 'relatedTo')
        self.obs["Hair"].addReference(self.obs["Mammal"], 'relatedTo')

        self.obs["Bone"].addReference(self.obs["Vertebrate"], 'relatedTo')
        self.obs["Vertebrate"].addReference(self.obs["Bone"], 'relatedTo')
        

        #content (must support IReferenceable)
        for doc in docs:
            self.folder.invokeFactory('ClassificationExample', id=doc)
            self.obs[doc] = getattr(self.folder, doc)
        
        #classification
        self.classify(self.obs["A"], self.obs["Mammal"])
        self.classify(self.obs["A"],self.obs["Hair"])
        self.classify(self.obs["B"],self.obs["Mammal"])
        self.classify(self.obs["C"],self.obs["Vertebrate"])
        self.classify(self.obs["D"],self.obs["Hair"])
        self.classify(self.obs["E"],self.obs["Bone"])
        self.classify(self.obs["F"],self.obs["Mammal"])
        self.classify(self.obs["F"],self.obs["Bone"])

    def testSkinInstallation(self):
        st = self.portal.portal_skins

        self.failUnless('PloneOntology' in st.objectIds())
    
    def testPreserveKeywordsOnReinstall(self):
        self.qi.uninstallProducts(['PloneOntology'])

        self.failUnless('kw_storage' in self.portal.objectIds())
        storage = self.portal.kw_storage

        self.failUnless("Mammal" in storage.objectIds())
        self.failUnless("Bone" in storage.objectIds())
        self.failUnless("Hair" in storage.objectIds())
        self.failUnless("Vertebrate" in storage.objectIds())
        self.failUnless("Structure" in storage.objectIds())

        self.qi.installProduct('PloneOntology')

        storage = self.portal.kw_storage

        self.failUnless("Mammal" in storage.objectIds())
        self.failUnless("Bone" in storage.objectIds())
        self.failUnless("Hair" in storage.objectIds())
        self.failUnless("Vertebrate" in storage.objectIds())
        self.failUnless("Structure" in storage.objectIds())
        
    ###### The tests ##########
        
if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(TestProductInstallation))
        return suite
