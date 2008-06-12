# -*- coding: utf-8 -*-
import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from unittest import TestCase
from Products.PloneOntology.owl import isXMLNCName, toXMLNCName

class TestOWL(TestCase):
    """Test the OWL module. Import and Export are tested separately.
    """

    ###### The tests ##########

    def testIsXMLNCNameEmpty(self):
        if isXMLNCName(''):
            self.fail()

    def testIsXMLNCNameSpaces(self):
        if isXMLNCName('with spaces'):
            self.fail()

    def testIsXMLNCNameNonASCII(self):
        if not isXMLNCName('äöüß'):
            self.fail()

    def testToXMLNCNameEmpty(self):
        self.assertEqual('', toXMLNCName(''))

    def testToXMLNCNameIdentity(self):
        self.assertEqual('test', toXMLNCName('test'))

    def testToXMLNCNameNonASCII(self):
        self.assertEqual('äöüß', toXMLNCName('äöüß'))

    def testToXMLNCNameNonNameStartChar(self):
        self.assertEqual('_00', toXMLNCName('00'))

    def testToXMLNCNameNonNameChar(self):
        self.assertEqual('nocolon', toXMLNCName('no:colon'))

    def testToXMLNCNameWhitespace(self):
        self.assertEqual('nowhitespace', toXMLNCName('no white\tspace\n'))

    def testToXMLNCNameUnderscoreDotMinus(self):
        self.assertEqual('_.-', toXMLNCName('_.-'))

    def testToXMLNCNameDotUnderscoreMinus(self):
        self.assertEqual('_._-', toXMLNCName('._-'))

    def testToXMLNCNameMinusDotUnderscore(self):
        self.assertEqual('_-._', toXMLNCName('-._'))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestOWL))
    return suite

if __name__ == '__main__':
    framework()
