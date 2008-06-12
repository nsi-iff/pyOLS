import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
# from Testing import ZopeTestCase
# from Products.CMFPlone.tests import PloneTestCase

# Install necessary products to portal
#ZopeTestCase.installProduct('Relations')
#ZopeTestCase.installProduct('PloneOntology')

from Products.PloneOntology.utils import _normalize

class TestUtils(unittest.TestCase):
    '''Test the utils module'''

    def testNormalize(self):
        self.assertEqual("thomas", _normalize("Thomas"))
        self.assertEqual("thomas", _normalize("Th om as"))
        self.assertEqual("thomas", _normalize("Th#{om-as"))
        self.assertEqual("tho123mas", _normalize("Tho-1.2.3m-as"))
                         
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestUtils))
    return suite

if __name__ == '__main__':
    framework()
