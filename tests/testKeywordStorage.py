import os, sys
import Testing

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

from xml.dom.minidom import parseString

ZopeTestCase.installProduct('Relations')
ZopeTestCase.installProduct('PloneOntology')

owl_skel = '''\
  <!DOCTYPE rdf:RDF [
    <!ENTITY owl "http://www.w3.org/2002/07/owl#"    >
    <!ENTITY xsd "http://www.w3.org/2001/XMLSchema#" >
    <!ENTITY dc  "http://www.purl.org/dc/elements/1.1/">
    <!ENTITY nip "http://www.neuroinf.de/ontology/0.1/">
  ]>
        
  <rdf:RDF
    xmlns:owl = "http://www.w3.org/2002/07/owl#"
    xmlns:rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rdfs= "http://www.w3.org/2000/01/rdf-schema#"
    xmlns:xsd = "http://www.w3.org/2001/XMLSchema#"
    xmlns:dc  = "http://purl.org/dc/elements/1.1/"
    xmlns:nip = "http://www.neuroinf.de/ontology/0.1/">
        
    <owl:Ontology rdf:about="">
      <rdfs:comment>OWL ontology for neuroinf.de</rdfs:comment>
      <rdfs:label>neuroinf.de ontology</rdfs:label>
    </owl:Ontology>
        
    <owl:AnnotationProperty rdf:about="&dc;title"/>
    <owl:AnnotationProperty rdf:about="&dc;description"/>
    <owl:AnnotationProperty rdf:about="&nip;weight"/>
    
  </rdf:RDF>
'''

class TestKeywordStorage(PloneTestCase.PloneTestCase):
    """Test the KeywordStorage class."""

    def afterSetUp(self):
        self.setRoles(['Manager'])
        self.qi = self.portal.portal_quickinstaller
        self.qi.installProduct('Relations')
        self.qi.installProduct('PloneOntology')

        self.rl = self.portal.relations_library
        self.ct = self.portal.portal_classification
        self.st = self.ct.getStorage()

        # Create template DOM
        self.dom = parseString(owl_skel)

        
    def testOWLImport(self):
        """OWL import tests."""
        expected_keywords = [ 'abdominal_ganglion',
                              'abducens_nerve',
                              'abducens_nerve_nucleus',
                              'abstract_mathematical_analysis_and_modeling',
                              'accessory_nerve',
                              'accessory_nerve_spinal_root_nucleus',
                              'accessory_oculomotor_nerve_nucleus',
                              'acetylcholin_rezeptor',
                              'acetylcholine',
                              'acetylcholine_muscarinic_receptor',
                              'acetylcholine_nicotinic_receptor',
                              'acetylcholine_receptor',
                              'cholinergic',
                              'computability_and_complexity',
                              'cranial_nerve',
                              'cranial_nerve_nucleus',
                              'invertebrate_structure',
                              'kernel_based_method',
                              'mathematical_and_theoretical_issue',
                              'muscarin',
                              'neurotransmitter_or_modulator',
                              'nicotine',
                              'nonlinear_dynamics',
                              'phase_space_analysis',
                              'receptor',
                              'statistical_mechanics'
                            ]
        expected_relations = [ 'childOf',
                               'parentOf',
                               'synonymOf',
                               'relatedTo'
                             ]
        owl_file = os.path.join(os.path.join(os.path.join(os.path.dirname(__file__), '..'), 'doc'), 'testOntology.owl')
        message  = self.st.importOWL(owl_file)

        ### check relations.
        # childOf
        self.assertEqual(self.ct.relations(self.rl), expected_relations)
        self.assertEqual(self.ct.getTypes   ('childOf'), ['transitive'])
        self.assertEqual(self.ct.getInverses('childOf'), ['parentOf'])
        self.assertEqual(self.ct.getWeight  ('childOf'), 0.5)
        # parentOf
        self.assertEqual(self.ct.getTypes   ('parentOf'), ['transitive'])
        self.assertEqual(self.ct.getInverses('parentOf'), ['childOf'])
        self.assertEqual(self.ct.getWeight  ('parentOf'), 0.5)
        # synonymOf
        self.assertEqual(self.ct.getTypes   ('synonymOf'), ['transitive', 'symmetric'])
        self.assertEqual(self.ct.getInverses('synonymOf'), [])
        self.assertEqual(self.ct.getWeight  ('synonymOf'), 1.0)
        # relatedTo
        self.assertEqual(self.ct.getTypes   ('relatedTo'), ['transitive', 'functional', 'inversefunctional'])
        self.assertEqual(self.ct.getInverses('relatedTo'), [])
        self.assertEqual(self.ct.getWeight  ('relatedTo'), 0.7)

        ### check keywords.
        self.assertEqual(self.ct.keywords(),  expected_keywords)
        # title, description, short additional description
        abdominal_ganglion = self.ct.getKeyword('abdominal_ganglion')
        self.assertEqual(abdominal_ganglion.title, 'Abdominal ganglion')
        self.assertEqual(abdominal_ganglion.getKwDescription(), 'The abdominal ganglion is abdominal')
        self.assertEqual(abdominal_ganglion.short_additional_description, 'The abdominal ganglion')

        ### check references.
        # childOf inverseOf parentOf
        invertebrate_structure = self.ct.getKeyword('invertebrate_structure')
        self.assertEqual(abdominal_ganglion.getRefs('childOf'), [invertebrate_structure])
        self.failUnless(abdominal_ganglion in invertebrate_structure.getRefs('parentOf'))
        # synonymOf symmetric
        acetylcholine_receptor = self.ct.getKeyword('acetylcholine_receptor')
        acetylcholin_rezeptor  = self.ct.getKeyword('acetylcholin_rezeptor')
        self.assertEqual(acetylcholine_receptor.getRefs('synonymOf'), [acetylcholin_rezeptor])
        self.assertEqual(acetylcholin_rezeptor.getRefs ('synonymOf'), [acetylcholine_receptor])
        # constraint message for relatedTo (functional, inversefunctional)
        self.assertEqual(message, "relatedTo(abducens_nerve,abducens_nerve_nucleus): Too many targets (2) for 'relatedTo'.\nrelatedTo(accessory_nerve_spinal_root_nucleus,accessory_nerve): Too many sources (2) for 'relatedTo'.\n")
        # violating references do not exist, but first ones do
        abducens_nerve  = self.ct.getKeyword('abducens_nerve')
        accessory_nerve = self.ct.getKeyword('accessory_nerve')
        self.assertEqual(abducens_nerve.getRefs('relatedTo'), [accessory_nerve])

    def testOWLExport(self):
        """OWL export tests."""
        owl_file = os.path.join(os.path.dirname(__file__), '..', 'doc', 'testOntology.owl')
        self.st.importOWL(owl_file)
        owl_string = self.st.exportOWL()
        owl_dom    = parseString(owl_string)

        entities = {}
        if owl_dom.doctype:
            doctype_entities = owl_dom.doctype.entities
            for i in range(len(doctype_entities)):
                if doctype_entities.item(i).hasChildNodes():
                    entities[doctype_entities.item(i).nodeName] = doctype_entities.item(i).firstChild.data

        # check if all relations are correct.
        owl_props = owl_dom.getElementsByTagName('owl:ObjectProperty')
        for rel in self.ct.relations(self.rl):
            p = [ps for ps in owl_props if ps.getAttribute('rdf:ID') == rel]
            self.assertEqual(len(p), 1)
            p = p[0]
            domains  = [d.getAttribute('rdf:resource') for d in p.getElementsByTagName('rdfs:domain')]
            ranges   = [r.getAttribute('rdf:resource') for r in p.getElementsByTagName('rdfs:range')]
            types    = [t.getAttribute('rdf:resource') for t in p.getElementsByTagName('rdf:type')]
            inverses = [i.getAttribute('rdf:resource') for i in p.getElementsByTagName('owl:inverseOf')]
            self.assertEqual(domains,  [entities['owl'] + 'Class'])
            self.assertEqual(ranges,   [entities['owl'] + 'Class'])
            self.assertEqual(types,    [entities['owl'] + self.st.owl_types[t] for t in self.ct.getTypes(rel)])
            self.assertEqual(inverses, ['#' + i for i in self.ct.getInverses(rel)])
            self.assertEqual(float(p.getElementsByTagName('nip:weight')[0].firstChild.data), self.ct.getWeight(rel))

        # check if all keywords are correct.
        owl_classes = owl_dom.getElementsByTagName('owl:Class')
        for kw in self.ct.keywords():
            keyword = self.ct.getKeyword(kw)
            c = [cl for cl in owl_classes if cl.getAttribute('rdf:ID') == kw]
            self.assertEqual(len(c), 1)
            c = c[0]
            if keyword.title:
                self.assertEqual(c.getElementsByTagName('dc:title')[0].firstChild.data.strip(), keyword.title)
            if keyword.short_additional_description:
                self.assertEqual(c.getElementsByTagName('rdfs:label')[0].firstChild.data.strip(), keyword.short_additional_description)
            if keyword.getKwDescription():
                self.assertEqual(c.getElementsByTagName('dc:description')[0].firstChild.data.strip(), keyword.getKwDescription())
            for rel in keyword.getRelationships():
                if rel == 'childOf':
                    self.assertEqual([superclass.getAttribute('rdf:resource') for superclass in c.getElementsByTagName('rdfs:subClassOf')], ['#' + parent.getId() for parent in keyword.getRefs('childOf')])
                elif rel == 'parentOf':
                    self.assertEqual([subclass.getAttribute('rdf:ID') for subclass in [cl for cl in owl_classes if '#' + kw in [sc.getAttribute('rdf:resource') for sc in cl.getElementsByTagName('rdfs:subClassOf')]]], [child.getId() for child in keyword.getRefs('parentOf')])
                elif rel == 'synonymOf':
                    self.assertEqual([eclass.getAttribute('rdf:resource') for eclass in reduce(lambda x,y: x+y, [cl.getElementsByTagName('owl:equivalentClass') for cl in owl_classes if kw == cl.getAttribute('rdf:about')])], ['#' + synonym.getId() for synonym in keyword.getRefs('synonymOf')])
                else:
                    self.assertEqual([el.getAttribute('rdf:resource') for el in c.getElementsByTagName(rel)], ['#' + ref.getId() for ref in keyword.getRefs(rel)])

def test_suite():
        from unittest import TestSuite, makeSuite
        suite = TestSuite()
        suite.addTest(makeSuite(TestKeywordStorage))
        return suite

if __name__ == '__main__':
    framework()
