from Products.CMFCore.utils import getToolByName
from Products.Relations.exception import ValidationException
import zExceptions
from xml.dom.minidom import parse, parseString, getDOMImplementation
import re

class OWLBase:
    owlTemplate = '''\
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

    def __init__(self):
        self._dom = parseString(self.owlTemplate)

        if self._dom.doctype:
            self._dom.doctype.name = 'rdf:RDF'
        
        self._entities = {}
        self.ensureEntities()

    def getDOM(self):
        return self._dom

    def getEntities(self):
        return self._entities

    def ensureEntities(self):
        """Collect XML entities and ensure existance of &owl; and &nip; entities.
        """
        if self._dom.doctype:
            doctype_entities = self._dom.doctype.entities
            for i in range(len(doctype_entities)):
                if doctype_entities.item(i).hasChildNodes():
                    self._entities[doctype_entities.item(i).nodeName] = doctype_entities.item(i).firstChild.data
        if not self._entities.has_key('owl'):
            self._entities['owl'] = 'http://www.w3.org/2002/07/owl#'
        if not self._entities.has_key('nip'):
            self._entities['nip'] = 'http://www.neuroinf.de/ontology/0.1/'

            
class OWLExporter(OWLBase):
        
    def serialize(self):
        return self.getDOM().toprettyxml()
    
    def generateClass(self, name, superclasses=[], labels={}, title="",
                      description="", classproperties=[]
                     ):
        """
        Return an OWL class element for class 'name' which is a subclass
        of every class in 'superclasses'. The class is labelled for each
        mapping of an ISO639 language code to a label in 'labels'.
        DublinCore 'title' and 'description' are annotated if non-empty.
        The class gets a property for each tuple of property name and class
        name in 'classproperties'.
        """
        cl = self._dom.createElement('owl:Class')
        cl.setAttribute('rdf:ID', name)

        for superclass in superclasses:
            subclassof = self._dom.createElement('rdfs:subClassOf')
            subclassof.setAttribute('rdf:resource', '#' + superclass)
            cl.appendChild(subclassof)

        for (lang, label) in labels.iteritems():
            l = self._dom.createElement('rdfs:label')
            l.setAttribute('xml:lang', lang)
            l.appendChild(self._dom.createTextNode(label))
            cl.appendChild(l)

        if title:
            t = self._dom.createElement('dc:title')
            t.appendChild(self._dom.createTextNode(title))
            cl.appendChild(t)

        if description:
            d = self._dom.createElement('dc:description')
            d.appendChild(self._dom.createTextNode(description))
            cl.appendChild(d)

        for (prop, propclass) in classproperties:
            p = self._dom.createElement(prop)
            p.setAttribute('rdf:resource', '#' + propclass)
            cl.appendChild(p)

        self._dom.documentElement.appendChild(cl)

    def generateEquivalentClass(self, class1, class2):
        """
        Return an OWL class element saying about 'class1' that it is
        equivalent to 'class2'.
        """
        eq  = self._dom.createElement('owl:Class')
        eqc = self._dom.createElement('owl:equivalentClass')
        eq.setAttribute('rdf:about', class1)
        eqc.setAttribute('rdf:resource', '#' + class2)
        eq.appendChild(eqc)

        self._dom.documentElement.appendChild(eq)

    def generateObjectProperty(self, name, types=[], inverses=[], domains=[], ranges=[],
                               labels={}, title="", description="",
                               propertyproperties=[]
                               ):
        """
        Return an OWL object property element for property 'name' with
        'types', 'iverses', 'domains' and 'ranges'. 'types' is a list of
        OWL type strings, e.g. ['&owl;TransitiveProperty',
        '&owl;SymmetricProperty']. 'inverses' is a list of inverse
        properties, e.g. name='parentOf', inverses=['childOf']. The
        property is labelled for each mapping of an ISO693 language code to
        label in 'labels'. DublinCore 'title' and 'description' are
        annotated if non-empty. The property gets a datatype property for
        each tuple of property name and string in 'propertyproperties'.
        """
        op = self._dom.createElement('owl:ObjectProperty')
        op.setAttribute('rdf:ID', name)
        for type in types:
            t = self._dom.createElement('rdf:type')
            t.setAttribute('rdf:resource', type)
            op.appendChild(t)

        for inverse in inverses:
            i = self._dom.createElement('owl:inverseOf')
            i.setAttribute('rdf:resource', '#' + inverse)
            op.appendChild(i)

        for domain in domains:
            d = self._dom.createElement('rdfs:domain')
            d.setAttribute('rdf:resource', domain)
            op.appendChild(d)

        for range in ranges:
            r = self._dom.createElement('rdfs:range')
            r.setAttribute('rdf:resource', range)
            op.appendChild(r)

        for (lang, label) in labels.iteritems():
            l = self._dom.createElement('rdfs:label')
            l.setAttribute('xml:lang', lang)
            l.appendChild(self._dom.createTextNode(label))
            op.appendChild(l)

        if title:
            t = self._dom.createElement('dc:title')
            t.appendChild(self._dom.createTextNode(title))
            op.appendChild(t)

        if description:
            d = self._dom.createElement('dc:description')
            d.appendChild(self._dom.createTextNode(description))
            op.appendChild(d)

        for (prop, string) in propertyproperties:
            p = self._dom.createElement(prop)
            p.appendChild(self._dom.createTextNode(string))
            op.appendChild(p)

        self._dom.documentElement.appendChild(op)



class OWLImporter(OWLBase):
    def __init__(self, context, file=None):
        self._context = context # acquisition context for finding tools

        OWLBase.__init__(self)
        
        if file is not None:
            self._dom = parse(file)

            if self._dom.doctype:
                self._dom.doctype.name = 'rdf:RDF'

            self.ensureEntities()
            
        self._props = []
        self.ensureBuiltinProperties()
        
    def objectProperties(self):
        """Return known non builtin relations"""
        return self._props

    def getBuiltinProperties(self):
        return [ 'childOf', 'parentOf', 'synonymOf' ]

    def ensureBuiltinProperties(self):
        """Ensure existance of OWL built-in relations
        
        rdfs:subClassOf     -- childOf <-> parentOf
        owl:equivalentClass -- synonymOf
        """
        ct = getToolByName(self._context, 'portal_classification')
        
        try:
            ct.getRelation('childOf')
        except KeyError:
            ct.addRelation('childOf'  , 1.0, ['transitive'], ['parentOf'])

        try:
            ct.getRelation('synonymOf')
        except KeyError:
            ct.addRelation('synonymOf', 1.0, ['transitive', 'symmetric'])
            
    def importProperties(self):
        for owlObjectProperty in self._dom.getElementsByTagName('owl:ObjectProperty'):
            self.importObjectProperty(owlObjectProperty)

    def domainAndRangeAreClasses(self, prop):
        nsClass = self._entities['owl'] + 'Class'

        domainIsClass = nsClass in [ domain.getAttribute('rdf:resource') for domain in prop.getElementsByTagName('rdfs:domain') ]
        rangeIsClass = nsClass in [ range.getAttribute('rdf:resource') for range in prop.getElementsByTagName('rdfs:range') ]

        return domainIsClass and rangeIsClass
        
    def importObjectProperty(self, prop):
        ct = getToolByName(self._context, 'portal_classification')
        rid = prop.getAttribute('rdf:ID')

        if  self.domainAndRangeAreClasses(prop):
            try:
                rel = ct.getRelation(rid)
            except KeyError:
                rel = ct.addRelation(rid)

            if not rid in self.getBuiltinProperties():
                self._props.append(rid)
                
            owl_type = re.compile('^' + self._entities['owl'] + '(.*)Property$')
            types = []
            for type in prop.getElementsByTagName('rdf:type'):
                match = owl_type.search(type.getAttribute('rdf:resource'))
                if match:
                    types.append(match.group(1).lower())

            ct.setTypes(rid, types)

            inverses = []
            for inverse in prop.getElementsByTagName('owl:inverseOf'):
                inverses.append(inverse.getAttribute('rdf:resource').strip("#"))

            ct.setInverses(rid, inverses)

            weights = prop.getElementsByTagName('nip:weight')
            if weights and weights[0].firstChild:
                weight = float(weights[0].firstChild.data)
            else:
                weight = 1.0

            ct.setWeight(rid, weight)

            dctitle = prop.getElementsByTagName("dc:title")
            try:
                rel.setTitle(dctitle[0].firstChild.data)
            except:
                rel.setTitle(rel.getId())

            dcdescription = prop.getElementsByTagName("dc:description")
            try:
                rel.setDescription(dcdescription[0].firstChild.data)
            except:
                rel.setDescription("")

            return rid

    def importClasses(self):
        error_string = ''
        for owlClass in self._dom.getElementsByTagName('owl:Class'):
            error_string = error_string + \
                           self.importClass(owlClass)

        return error_string
            
    def importClass(self, cl):
        error_string=""
        ct = getToolByName(self._context, 'portal_classification')
        kid = cl.getAttribute('rdf:ID')

        if kid:
            try:
                kw = ct.getKeyword(kid)
            except KeyError:
                kw = ct.addKeyword(kid)

            short_additional_description = ''
            for label in cl.getElementsByTagName('rdfs:label'):
                # ignore language and use first value.
                if label.firstChild:
                    short_additional_description = label.firstChild.data.strip()
                    break

            kw.setShort_additional_description(short_additional_description)
                
            for superclass in cl.getElementsByTagName('rdfs:subClassOf'):
                src = kw.getId()
                dst = superclass.getAttribute('rdf:resource').strip("#")
                try:
                    ct.addReference(src, dst, 'childOf')
                except ValidationException, e:
                    error_string = error_string + "childOf(%s,%s): %s\n" % (src, dst, e.message)
                except zExceptions.NotFound:
                    error_string = error_string + "No such relation: childOf.\n"

            dctitle = cl.getElementsByTagName("dc:title")
            try:
                kw.setTitle(dctitle[0].firstChild.data.strip())
            except:
                kw.setTitle(kw.getId())

            dcdescription = cl.getElementsByTagName("dc:description")
            try:
                kw.setKwDescription(dcdescription[0].firstChild.data.strip())
            except:
                kw.setKwDescription("")

            for classObjectProperty in self.objectProperties():
                for prop in cl.getElementsByTagName(classObjectProperty):
                    src = kw.getId()
                    dst = prop.getAttribute('rdf:resource').strip('#')

                    try:
                        dstkw = ct.getKeyword(dst)
                    except KeyError:
                        ct.addKeyword(dst)

                    try:
                        ct.addReference(src, dst, prop.tagName)
                    except ValidationException, e:
                        error_string = error_string + "%s(%s,%s): %s\n" % (prop.tagName, src, dst, e.message)
                    except zExceptions.NotFound:
                        error_string = error_string + "No such relation: %s.\n" % prop.tagName

        if cl.hasAttribute('rdf:about'):
            for equivalentClass in cl.getElementsByTagName('owl:equivalentClass'):
                src = cl.getAttribute('rdf:about')
                dst = equivalentClass.getAttribute('rdf:resource').strip("#")
                try:
                    ct.addReference(src, dst, 'synonymOf')
                except ValidationException, e:
                    error_string = error_string + "synonymOf(%s,%s): %s\n" % (src, dst, e.message)
                except zExceptions.NotFound:
                    error_string = error_string + "No such relation: synonymOf.\n" % prop.tagName
                    
        return error_string

    
