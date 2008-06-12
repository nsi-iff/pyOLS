import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from producttest import PloneOntologyTestCase

from Products.PloneOntology.owl import OWLExporter

class TestOWLExporter(PloneOntologyTestCase):
    """Test the OWL export."""

    def afterSetUp(self):
        self.setRoles(['Manager'])

        self.exporter = OWLExporter()

    def testOWLExportGenerateClassDefault(self):
        self.exporter.generateClass("foo")
        cl = self.exporter.getDOM().documentElement.lastChild

        self.assertEqual('foo', cl.getAttribute('rdf:ID'))

    def testOWLExportGenerateClassSuperClasses(self):
        self.exporter.generateClass("foo", superclasses = ["bar", "blaz"])
        cl = self.exporter.getDOM().documentElement.lastChild

        super = cl.getElementsByTagName('rdfs:subClassOf')
        names = [c.getAttribute('rdf:resource') for c in super]
        names.sort()

        self.assertEqual(['#bar', '#blaz'], names)

    def testOWLExportGenerateClassLabels(self):
        self.exporter.generateClass("foo", labels = [('de','Honig'), ('en','honey')])
        cl = self.exporter.getDOM().documentElement.lastChild

        labels = cl.getElementsByTagName('rdfs:label')
        res = []
        for l in labels:
            res.append((l.getAttribute('xml:lang'), l.firstChild.data))

        res.sort()

        self.assertEqual([('de','Honig'), ('en', 'honey')], res)

    def testOWLExportGenerateClassDCAttributes(self):
        self.exporter.generateClass("foo", labels=[('en',"bar")], descriptions=[('en',"blaz")])
        cl = self.exporter.getDOM().documentElement.lastChild

        title = cl.getElementsByTagName('rdfs:label')
        self.assertEqual(1, title.length)
        self.assertEqual("bar", title.item(0).firstChild.data)

        desc = cl.getElementsByTagName('dc:description')
        self.assertEqual(1, desc.length)
        self.assertEqual("blaz", desc.item(0).firstChild.data)

    def testOWLExportGenerateEquivalentClass(self):
        self.exporter.generateEquivalentClass("foo", "bar")
        cl = self.exporter.getDOM().documentElement.lastChild

        self.assertEqual("#foo", cl.getAttribute('rdf:about'))

        ecl = cl.getElementsByTagName('owl:equivalentClass')
        self.assertEqual(1, ecl.length)
        self.assertEqual("#bar", ecl.item(0).getAttribute('rdf:resource'))

    def testOWLExportEnsureEntities(self):
        self.exporter.ensureEntities()

        self.assert_(self.exporter.getEntities().has_key('owl'))
        self.assert_(self.exporter.getEntities().has_key('nip'))

    def testOWLExportGenerateObjectPropertyDefault(self):
        self.exporter.generateObjectProperty("foo")
        prop = self.exporter.getDOM().documentElement.lastChild

        self.assertEqual("foo", prop.getAttribute("rdf:ID"))

    def testOWLExportGenerateObjectPropertyTypes(self):
        self.exporter.generateObjectProperty("foo", types=["bar", "blaz"])
        prop = self.exporter.getDOM().documentElement.lastChild

        types = prop.getElementsByTagName('rdf:type')
        names = [x.getAttribute('rdf:resource') for x in types]
        names.sort()

        self.assertEqual(["bar", "blaz"], names)

    def testOWLExportGenerateObjectPropertyInverses(self):
        self.exporter.generateObjectProperty("foo", inverses=["bar", "blaz"])
        prop = self.exporter.getDOM().documentElement.lastChild

        types = prop.getElementsByTagName('owl:inverseOf')
        names = [x.getAttribute('rdf:resource') for x in types]
        names.sort()

        self.assertEqual(["#bar", "#blaz"], names)

    def testOWLExportGenerateObjectPropertyDomains(self):
        self.exporter.generateObjectProperty("foo", domains=["bar", "blaz"])
        prop = self.exporter.getDOM().documentElement.lastChild

        types = prop.getElementsByTagName('rdfs:domain')
        names = [x.getAttribute('rdf:resource') for x in types]
        names.sort()

        self.assertEqual(["bar", "blaz"], names)

    def testOWLExportGenerateObjectPropertyRange(self):
        self.exporter.generateObjectProperty("foo", ranges=["bar", "blaz"])
        prop = self.exporter.getDOM().documentElement.lastChild

        types = prop.getElementsByTagName('rdfs:range')
        names = [x.getAttribute('rdf:resource') for x in types]
        names.sort()

        self.assertEqual(["bar", "blaz"], names)

    def testOWLExportGenerateObjectPropertyLabels(self):
        self.exporter.generateObjectProperty("foo", labels = [('de','Honig'), ('en','honey')])
        prop = self.exporter.getDOM().documentElement.lastChild

        labels = prop.getElementsByTagName('rdfs:label')
        res = []
        for l in labels:
            res.append((l.getAttribute('xml:lang'), l.firstChild.data))

        res.sort()

        self.assertEqual([('de','Honig'), ('en', 'honey')], res)

    def testOWLExportGenerateObjectPropertyDCAttributes(self):
        self.exporter.generateObjectProperty("foo", labels=[('en',"bar")], descriptions=[('en',"blaz")])
        prop = self.exporter.getDOM().documentElement.lastChild

        title = prop.getElementsByTagName('rdfs:label')
        self.assertEqual(1, title.length)
        self.assertEqual("bar", title.item(0).firstChild.data)

        desc = prop.getElementsByTagName('dc:description')
        self.assertEqual(1, desc.length)
        self.assertEqual("blaz", desc.item(0).firstChild.data)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestOWLExporter))
    return suite

if __name__ == '__main__':
    framework()
