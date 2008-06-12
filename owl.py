from Products.CMFCore.utils import getToolByName
from Products.Relations.exception import ValidationException
from zExceptions import NotFound
from xml.dom.minidom import parse, parseString, getDOMImplementation
import re

def parseURIRef(uriRef):
    # FIXME: Do we see xml entities (for context)?
    (fragmentContext, fragment) = re.match('([^#]*)#?(.*)', uriRef).groups()
    return {'fragmentContext':fragmentContext, 'fragment':fragment}

def generateURIRef(fragment, fragmentContext=""):
    return fragmentContext + '#' + fragment

def isXMLNCName(name):
    # 'name' is (non-empty) XML NCName
    # TODO: Use proper unicode character classes. Current version is too
    # restrictive. See <http://www.w3.org/TR/REC-xml-names/#NT-NCName>.
    return re.match('^[A-Za-z_][A-Za-z0-9._-]*$', name)

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
      xmlns:nip = "http://www.neuroinf.de/ontology/0.1/"
      xmlns     = "http://www.neuroinf.de/ontology/0.1/kw_storage.owl#"
      xml:base  = "http://www.neuroinf.de/ontology/0.1/kw_storage.owl">
    
      <owl:Ontology rdf:about="">
        <rdfs:label xml:lang="en">neuroinf.de ontology</rdfs:label>
        <rdfs:comment xml:lang="en">OWL ontology for neuroinf.de</rdfs:comment>
      </owl:Ontology>
    
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

    def generateClass(self, name, superclasses=[], labels=[], comments=[],
                      descriptions=[], classproperties=[]
                     ):
        """Return an OWL class element for class 'name' which is a subclass of every class in 'superclasses'.
        The class is RDFS labelled, commented on and DublinCore described for each pair of an ISO639 language code to a label in 'labels', a comment in 'comments' or a description in 'descriptions' respectively. The class gets a property for each pair of property name and class name in 'classproperties'.
        """
        cl = self._dom.createElement('owl:Class')
        cl.setAttribute('rdf:ID', name)

        for superclass in superclasses:
            subclassof = self._dom.createElement('rdfs:subClassOf')
            subclassof.setAttribute('rdf:resource', generateURIRef(superclass))
            cl.appendChild(subclassof)

        for (lang, label) in labels:
            l = self._dom.createElement('rdfs:label')
            l.setAttribute('xml:lang', lang)
            l.appendChild(self._dom.createTextNode(label))
            cl.appendChild(l)

        for (lang, comment) in comments:
            c = self._dom.createElement('rdfs:comment')
            c.setAttribute('xml:lang', lang)
            c.appendChild(self._dom.createTextNode(comment))
            cl.appendChild(c)

        for (lang, description) in descriptions:
            d = self._dom.createElement('dc:description')
            d.setAttribute('xml:lang', lang)
            d.appendChild(self._dom.createTextNode(description))
            cl.appendChild(d)

        for (prop, propclass) in classproperties:
            p = self._dom.createElement(prop)
            p.setAttribute('rdf:resource', generateURIRef(propclass))
            cl.appendChild(p)

        self._dom.documentElement.appendChild(cl)

    def generateEquivalentClass(self, class1, class2):
        """Return an OWL class element saying about 'class1' that it is equivalent to 'class2'.
        """
        eq  = self._dom.createElement('owl:Class')
        eqc = self._dom.createElement('owl:equivalentClass')
        eq.setAttribute('rdf:about', generateURIRef(class1))
        eqc.setAttribute('rdf:resource', generateURIRef(class2))
        eq.appendChild(eqc)

        self._dom.documentElement.appendChild(eq)

    def generateObjectProperty(self, name, types=[], inverses=[], domains=[], ranges=[],
                               labels=[], comments=[], descriptions=[],
                               propertyproperties=[]
                               ):
        """Return an OWL object property element for property 'name' with 'types', 'iverses', 'domains' and 'ranges'.

        'types' is a list of OWL type strings, e.g. ['&owl;TransitiveProperty', '&owl;SymmetricProperty']. 'inverses' is a list of inverse properties, e.g. name='parentOf', inverses=['childOf']. The property is RDFS labelled, commented on and DublinCore described for each pair of an ISO639 language code to a label in 'labels', a comment in 'comments' or a description in 'descriptions' respectively. The property gets a datatype property for each pair of property name and string in 'propertyproperties'.
        """
        op = self._dom.createElement('owl:ObjectProperty')
        op.setAttribute('rdf:ID', name)
        for type in types:
            t = self._dom.createElement('rdf:type')
            t.setAttribute('rdf:resource', type)
            op.appendChild(t)

        for inverse in inverses:
            i = self._dom.createElement('owl:inverseOf')
            i.setAttribute('rdf:resource', generateURIRef(inverse))
            op.appendChild(i)

        for domain in domains:
            d = self._dom.createElement('rdfs:domain')
            d.setAttribute('rdf:resource', domain)
            op.appendChild(d)

        for range in ranges:
            r = self._dom.createElement('rdfs:range')
            r.setAttribute('rdf:resource', range)
            op.appendChild(r)

        for (lang, label) in labels:
            l = self._dom.createElement('rdfs:label')
            l.setAttribute('xml:lang', lang)
            l.appendChild(self._dom.createTextNode(label))
            op.appendChild(l)

        for (lang, comment) in comments:
            c = self._dom.createElement('rdfs:comment')
            c.setAttribute('xml:lang', lang)
            c.appendChild(self._dom.createTextNode(comment))
            op.appendChild(c)

        for (lang, description) in descriptions:
            d = self._dom.createElement('dc:description')
            d.setAttribute('xml:lang', lang)
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
        """Ensure existance of OWL built-in relations.

        rdfs:subClassOf     -- childOf <validation.register(PartialUrlValidator('isPartialUrl'))-> parentOf
        owl:equivalentClass -- synonymOf
        """
        ct = getToolByName(self._context, 'portal_classification')

        try:
            ct.getRelation('childOf')
        except ValueError:
            ct.addRelation('childOf'  , 1.0, ['transitive'], ['parentOf'])
        except NotFound:
            ct.addRelation('childOf'  , 1.0, ['transitive'], ['parentOf'])

        try:
            ct.getRelation('synonymOf')
        except ValueError:
            ct.addRelation('synonymOf', 1.0, ['transitive', 'symmetric'])
        except NotFound:
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
            except ValueError:
                rel = ct.addRelation(rid)
            except NotFound:
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
                inverses.append(parseURIRef(inverse.getAttribute('rdf:resource'))['fragment'])

            ct.setInverses(rid, inverses)

            weights = prop.getElementsByTagName('nip:weight')
            if weights and weights[0].firstChild:
                weight = float(weights[0].firstChild.data)
            else:
                weight = 1.0

            ct.setWeight(rid, weight)

            labels = prop.getElementsByTagName("rdfs:label")
            try:
                rel.setTitle(labels[0].firstChild.data)
            except:
                rel.setTitle(rel.getId())

            descriptions = prop.getElementsByTagName("dc:description")
            try:
                rel.setDescription(descriptions[0].firstChild.data)
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
            except NotFound:
                try:
                    kw = ct.addKeyword(kid)
                except ValidationException, e:
                    error_string = error_string + "Cannot create keyword '%s': %s" % (kid, e)
                    return error_string
                except NameError, e: # this should never happen.
                    error_string = error_string + "BUG: Cannot create keyword '%s': %s" % (kid, e)
                    return error_string

            for label in cl.getElementsByTagName('rdfs:label'):
                # ignore language and use first value.
                if label.firstChild:
                    kw.setTitle(label.firstChild.data.strip())
                    break

            for comment in cl.getElementsByTagName('rdfs:comment'):
                # ignore language and use first value.
                if comment.firstChild:
                    kw.setShortAdditionalDescription(comment.firstChild.data.strip())
                    break

            for description in cl.getElementsByTagName('dc:description'):
                # ignore language and use first value.
                if description.firstChild:
                    kw.setKwDescription(description.firstChild.data.strip())
                    break

            kw.reindexObject()

            for superclass in cl.getElementsByTagName('rdfs:subClassOf'):
                src = kw.getName()
                dsts = []
                if superclass.hasAttribute('rdf:resource'):
                    dsts.append(parseURIRef(superclass.getAttribute('rdf:resource'))['fragment'])
                else:
                    for cls in superclass.getElementsByTagName('owl:Class'):
                        if cls.hasAttribute('rdf:about'):
                            dsts.append(parseURIRef(cls.getAttribute('rdf:about'))['fragment'])
                        elif cls.hasAttribute('rdf:ID'):
                            dsts.append(cls.getAttribute('rdf:ID'))

                for dst in dsts:
                    try:
                        ct.addReference(src, dst, 'childOf')
                    except ValidationException, e:
                        error_string = error_string + "childOf(%s,%s): %s\n" % (src, dst, e.message)
                    except NotFound:
                        error_string = error_string + "No such relation: childOf.\n"

            for classObjectProperty in self.objectProperties():
                for prop in cl.getElementsByTagName(classObjectProperty):
                    src = kw.getName()
                    dst = parseURIRef(prop.getAttribute('rdf:resource'))['fragment']

                    try:
                        ct.getKeyword(dst)
                    except NotFound:
                        try:
                            ct.addKeyword(dst)
                        except ValidationException, e:
                            error_string = error_string + "Cannot create keyword '%s': %s" % (dst, e)
                            continue
                        except NameError, e: # this should never happen.
                            error_string = error_string + "BUG: Cannot create keyword '%s': %s" % (dst, e)
                            continue

                    try:
                        ct.addReference(src, dst, prop.tagName)
                    except ValidationException, e:
                        error_string = error_string + "%s(%s,%s): %s\n" % (prop.tagName, src, dst, e.message)
                    except NotFound:
                        error_string = error_string + "No such relation: %s.\n" % prop.tagName

        if cl.hasAttribute('rdf:about'):
            for equivalentClass in cl.getElementsByTagName('owl:equivalentClass'):
                src = parseURIRef(cl.getAttribute('rdf:about'))['fragment']
                dst = parseURIRef(equivalentClass.getAttribute('rdf:resource'))['fragment']

                try:
                    ct.getKeyword(src)
                except NotFound:
                    try:
                        ct.addKeyword(src)
                    except ValidationException, e:
                        error_string = error_string + "Cannot create keyword '%s': %s" % (src, e)
                        return error_string
                    except NameError, e: # this should never happen.
                        error_string = error_string + "BUG: Cannot create keyword '%s': %s" % (src, e)
                        return error_string

                try:
                    ct.getKeyword(dst)
                except NotFound:
                    try:
                        ct.addKeyword(dst)
                    except ValidationException, e:
                        error_string = error_string + "Cannot create keyword '%s': %s" % (dst, e)
                        return error_string
                    except NameError, e: # this should never happen.
                        error_string = error_string + "BUG: Cannot create keyword '%s': %s" % (dst, e)
                        return error_string

                try:
                    ct.addReference(src, dst, 'synonymOf')
                except ValidationException, e:
                    error_string = error_string + "synonymOf(%s,%s): %s\n" % (src, dst, e.message)
                except NotFound:
                    error_string = error_string + "No such relation: synonymOf.\n"

        return error_string
