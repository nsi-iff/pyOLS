import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from producttest import PloneOntologyTestCase

from Products.PloneOntology.owl import OWLExporter, OWLImporter
from zExceptions import NotFound

class TestOWLImporter(PloneOntologyTestCase):
    """Test the OWL import."""

    def afterSetUp(self):
        self.setRoles(['Manager'])

        self.ct = self.portal.portal_classification

        self.exporter = OWLExporter()
        self.importer = OWLImporter(self.portal)

    def testOWLImporterObjectProperty(self):
        owl = self.exporter.getEntities()['owl']

        self.exporter.generateObjectProperty("synonymOf",
                                             types = [owl+'TransitiveProperty', owl+'SymmetricProperty'],
                                             inverses = ['foo'],
                                             domains = [owl+'Class'],
                                             ranges = [owl+'Class'],
                                             labels = [('en',"footitle")],
                                             comments =  [('de','Honig'), ('en','honey')],
                                             descriptions = [('en',"foodescription")],
                                             propertyproperties = [("nip:weight", "0.7")]
                                             )

        prop = self.exporter.getDOM().documentElement.lastChild

        self.importer.importObjectProperty(prop)

        try:
            rel = self.ct.getRelation('synonymOf')
        except NotFound:
            self.fail("Necessary relation not created on import.")

        self.assert_('transitive' in self.ct.getTypes('synonymOf'))
        self.assert_('symmetric' in self.ct.getTypes('synonymOf'))
        self.assertEqual(['foo'], self.ct.getInverses('synonymOf'))
        self.assertAlmostEqual(0.7, self.ct.getWeight('synonymOf'))
        # titles are used as names, labels are ignored, see owl.py
        self.assertEqual("synonymOf", rel.Title())
        self.assertEqual("foodescription", rel.Description())

    def testOWLImporterObjectPropertyIgnoreNonOWLClassDomain(self):
        owl = self.exporter.getEntities()['owl']
        self.exporter.generateObjectProperty("foo1", domains=[owl+'Instance'], ranges=[owl+'Class'])
        prop = self.exporter.getDOM().documentElement.lastChild
        self.importer.importObjectProperty(prop)
        self.assertRaises(NotFound, self.ct.getRelation, "foo1")

    def testOWLImporterObjectPropertyIgnoreNonOWLClassRange(self):
        owl = self.exporter.getEntities()['owl']
        self.exporter.generateObjectProperty("foo1", ranges=[owl+'Instance'], domains=[owl+'Class'])
        prop = self.exporter.getDOM().documentElement.lastChild
        self.importer.importObjectProperty(prop)
        self.assertRaises(NotFound, self.ct.getRelation, "foo1")

    def testOWLImporterObjectPropertyAccumulateNonBuiltins(self):
        owl = self.exporter.getEntities()['owl']
        self.exporter.generateObjectProperty("authorOf", ranges=[owl+'Class'], domains=[owl+'Class'])
        prop = self.exporter.getDOM().documentElement.lastChild
        self.importer.importObjectProperty(prop)

        self.assertEquals(['authorOf'], self.importer.objectProperties())

        self.exporter.generateObjectProperty("publisher", ranges=[owl+'Class'], domains=[owl+'Class'])
        prop = self.exporter.getDOM().documentElement.lastChild
        self.importer.importObjectProperty(prop)

        props = self.importer.objectProperties()
        props.sort()

        self.assertEquals(['authorOf', 'publisher'], self.importer.objectProperties())

    def testOWLImporterBuiltinProperties(self):
        try:
            self.ct.getRelation("childOf")
            self.ct.getRelation("parentOf")
            self.ct.getRelation("synonymOf")
        except NotFound:
            self.fail("At least one builtin relation is missing after creation of an importer")

    def testOWLImporterClass(self):
        self.ct.addRelation("authorOf")
        self.ct.addRelation("publisher")
        self.importer._props = ['authorOf', 'publisher']
        self.exporter.generateClass("Foo",
                                    superclasses = ["Bar", "Blaz"],
                                    labels = [('en',"footitle")],
                                    comments = [('de','Honig'), ('en','honey')],
                                    descriptions = [('en',"foodescription")],
                                    classproperties=[("authorOf", "Bonk"), ('publisher', "Gargle")]
                                    )
        cl = self.exporter.getDOM().documentElement.lastChild
        self.importer.importClass(cl)

        try:
            kw = self.ct.getKeyword("Foo")
        except NotFound:
            self.fail("Necessary keyword not created on import.")

        self.assertEqual("footitle", kw.Title())
        self.assertEqual("foodescription", kw.getKwDescription())

        try:
            self.ct.getKeyword("Bar")
            self.ct.getKeyword("Blaz")
        except NotFound:
            self.fail("Necessary keyword not created on import (superclasses).")

        super = kw.getReferences("childOf")
        super = [x.getName() for x in super]
        super.sort()

        self.assertEqual(["Bar", "Blaz"], super)

        try:
            self.ct.getKeyword("Bonk")
            self.ct.getKeyword("Gargle")
        except NotFound:
            self.fail("Necessary keyword not created on import (properties).")

        syn = kw.getReferences("authorOf")
        syn = [x.getName() for x in syn]

        self.assertEqual(['Bonk'], syn)

        syn = kw.getReferences("publisher")
        syn = [x.getName() for x in syn]

        self.assertEqual(['Gargle'], syn)

    def testOWLImporterClassEquivalentClass(self):
        foo = self.ct.addKeyword("Foo")
        bar = self.ct.addKeyword("Bar")
        self.exporter.generateEquivalentClass("Foo", "Bar")
        cl = self.exporter.getDOM().documentElement.lastChild
        self.importer.importClass(cl)

        self.assertEquals(["Bar"], [x.getName() for x in foo.getReferences('synonymOf')])

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestOWLImporter))
    return suite

if __name__ == '__main__':
    framework()
