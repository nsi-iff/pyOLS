from pyols.log import log
from pyols.util import to_unicode

from xml.dom.minidom import parse, parseString, getDOMImplementation
import re

# Character classes and regular expression for XML NCName. See <http://www.w3.org/TR/REC-xml-names/#NT-NCName>.
BaseChar = u'\u0041-\u005A\u0061-\u007A\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF\u0100-\u0131\u0134-\u013E\u0141-\u0148\u014A-\u017E\u0180-\u01C3\u01CD-\u01F0\u01F4-\u01F5\u01FA-\u0217\u0250-\u02A8\u02BB-\u02C1\u0386\u0388-\u038A\u038C\u038E-\u03A1\u03A3-\u03CE\u03D0-\u03D6\u03DA\u03DC\u03DE\u03E0\u03E2-\u03F3\u0401-\u040C\u040E-\u044F\u0451-\u045C\u045E-\u0481\u0490-\u04C4\u04C7-\u04C8\u04CB-\u04CC\u04D0-\u04EB\u04EE-\u04F5\u04F8-\u04F9\u0531-\u0556\u0559\u0561-\u0586\u05D0-\u05EA\u05F0-\u05F2\u0621-\u063A\u0641-\u064A\u0671-\u06B7\u06BA-\u06BE\u06C0-\u06CE\u06D0-\u06D3\u06D5\u06E5-\u06E6\u0905-\u0939\u093D\u0958-\u0961\u0985-\u098C\u098F-\u0990\u0993-\u09A8\u09AA-\u09B0\u09B2\u09B6-\u09B9\u09DC-\u09DD\u09DF-\u09E1\u09F0-\u09F1\u0A05-\u0A0A\u0A0F-\u0A10\u0A13-\u0A28\u0A2A-\u0A30\u0A32-\u0A33\u0A35-\u0A36\u0A38-\u0A39\u0A59-\u0A5C\u0A5E\u0A72-\u0A74\u0A85-\u0A8B\u0A8D\u0A8F-\u0A91\u0A93-\u0AA8\u0AAA-\u0AB0\u0AB2-\u0AB3\u0AB5-\u0AB9\u0ABD\u0AE0\u0B05-\u0B0C\u0B0F-\u0B10\u0B13-\u0B28\u0B2A-\u0B30\u0B32-\u0B33\u0B36-\u0B39\u0B3D\u0B5C-\u0B5D\u0B5F-\u0B61\u0B85-\u0B8A\u0B8E-\u0B90\u0B92-\u0B95\u0B99-\u0B9A\u0B9C\u0B9E-\u0B9F\u0BA3-\u0BA4\u0BA8-\u0BAA\u0BAE-\u0BB5\u0BB7-\u0BB9\u0C05-\u0C0C\u0C0E-\u0C10\u0C12-\u0C28\u0C2A-\u0C33\u0C35-\u0C39\u0C60-\u0C61\u0C85-\u0C8C\u0C8E-\u0C90\u0C92-\u0CA8\u0CAA-\u0CB3\u0CB5-\u0CB9\u0CDE\u0CE0-\u0CE1\u0D05-\u0D0C\u0D0E-\u0D10\u0D12-\u0D28\u0D2A-\u0D39\u0D60-\u0D61\u0E01-\u0E2E\u0E30\u0E32-\u0E33\u0E40-\u0E45\u0E81-\u0E82\u0E84\u0E87-\u0E88\u0E8A\u0E8D\u0E94-\u0E97\u0E99-\u0E9F\u0EA1-\u0EA3\u0EA5\u0EA7\u0EAA-\u0EAB\u0EAD-\u0EAE\u0EB0\u0EB2-\u0EB3\u0EBD\u0EC0-\u0EC4\u0F40-\u0F47\u0F49-\u0F69\u10A0-\u10C5\u10D0-\u10F6\u1100\u1102-\u1103\u1105-\u1107\u1109\u110B-\u110C\u110E-\u1112\u113C\u113E\u1140\u114C\u114E\u1150\u1154-\u1155\u1159\u115F-\u1161\u1163\u1165\u1167\u1169\u116D-\u116E\u1172-\u1173\u1175\u119E\u11A8\u11AB\u11AE-\u11AF\u11B7-\u11B8\u11BA\u11BC-\u11C2\u11EB\u11F0\u11F9\u1E00-\u1E9B\u1EA0-\u1EF9\u1F00-\u1F15\u1F18-\u1F1D\u1F20-\u1F45\u1F48-\u1F4D\u1F50-\u1F57\u1F59\u1F5B\u1F5D\u1F5F-\u1F7D\u1F80-\u1FB4\u1FB6-\u1FBC\u1FBE\u1FC2-\u1FC4\u1FC6-\u1FCC\u1FD0-\u1FD3\u1FD6-\u1FDB\u1FE0-\u1FEC\u1FF2-\u1FF4\u1FF6-\u1FFC\u2126\u212A-\u212B\u212E\u2180-\u2182\u3041-\u3094\u30A1-\u30FA\u3105-\u312C\uAC00-\uD7A3'
CombiningChar = u'\u0300-\u0345\u0360-\u0361\u0483-\u0486\u0591-\u05A1\u05A3-\u05B9\u05BB-\u05BD\u05BF\u05C1-\u05C2\u05C4\u064B-\u0652\u0670\u06D6-\u06DC\u06DD-\u06DF\u06E0-\u06E4\u06E7-\u06E8\u06EA-\u06ED\u0901-\u0903\u093C\u093E-\u094C\u094D\u0951-\u0954\u0962-\u0963\u0981-\u0983\u09BC\u09BE\u09BF\u09C0-\u09C4\u09C7-\u09C8\u09CB-\u09CD\u09D7\u09E2-\u09E3\u0A02\u0A3C\u0A3E\u0A3F\u0A40-\u0A42\u0A47-\u0A48\u0A4B-\u0A4D\u0A70-\u0A71\u0A81-\u0A83\u0ABC\u0ABE-\u0AC5\u0AC7-\u0AC9\u0ACB-\u0ACD\u0B01-\u0B03\u0B3C\u0B3E-\u0B43\u0B47-\u0B48\u0B4B-\u0B4D\u0B56-\u0B57\u0B82-\u0B83\u0BBE-\u0BC2\u0BC6-\u0BC8\u0BCA-\u0BCD\u0BD7\u0C01-\u0C03\u0C3E-\u0C44\u0C46-\u0C48\u0C4A-\u0C4D\u0C55-\u0C56\u0C82-\u0C83\u0CBE-\u0CC4\u0CC6-\u0CC8\u0CCA-\u0CCD\u0CD5-\u0CD6\u0D02-\u0D03\u0D3E-\u0D43\u0D46-\u0D48\u0D4A-\u0D4D\u0D57\u0E31\u0E34-\u0E3A\u0E47-\u0E4E\u0EB1\u0EB4-\u0EB9\u0EBB-\u0EBC\u0EC8-\u0ECD\u0F18-\u0F19\u0F35\u0F37\u0F39\u0F3E\u0F3F\u0F71-\u0F84\u0F86-\u0F8B\u0F90-\u0F95\u0F97\u0F99-\u0FAD\u0FB1-\u0FB7\u0FB9\u20D0-\u20DC\u20E1\u302A-\u302F\u3099\u309A'
Digit = u'\u0030-\u0039\u0660-\u0669\u06F0-\u06F9\u0966-\u096F\u09E6-\u09EF\u0A66-\u0A6F\u0AE6-\u0AEF\u0B66-\u0B6F\u0BE7-\u0BEF\u0C66-\u0C6F\u0CE6-\u0CEF\u0D66-\u0D6F\u0E50-\u0E59\u0ED0-\u0ED9\u0F20-\u0F29'
Extender = u'\u00B7\u02D0\u02D1\u0387\u0640\u0E46\u0EC6\u3005\u3031-\u3035\u309D-\u309E\u30FC-\u30FE'
Ideographic = u'\u4E00-\u9FA5\u3007\u3021-\u3029'
Letter = BaseChar + Ideographic
NCNameChar = Letter + Digit + CombiningChar + Extender + u'\u002D\u002E\u005F'
NCNameStartChar = Letter + u'\u005F'
NCName = '[' + NCNameStartChar + ']' + '[' + NCNameChar + ']*'

def isXMLNCName(name):
    """'name' is a (non-empty) XML NCName."""
    name = to_unicode(name)
    return re.match('^' + NCName + '$', name, re.UNICODE)

def toXMLNCName(name):
    """Convert 'name' into an XML NCName."""
    name = [c for c in to_unicode(c) if re.match('[' + NCNameChar + ']', c, re.UNICODE)]
    if name and not re.match('[' + NCNameStartChar + ']', name[0], re.UNICODE):
        name = ['_'] + name
    return ''.join(name)

def parseURIRef(uriRef):
    (fragmentContext, fragment) = re.match('([^#]*)#?(.*)', uriRef).groups()
    return {'fragmentContext':fragmentContext, 'fragment':fragment}

def generateURIRef(fragment, fragmentContext=""):
    return fragmentContext + '#' + fragment

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

    ### OWL type strings. External for unit tests.
    owl_types = {'transitive'        : 'TransitiveProperty',
                 'symmetric'         : 'SymmetricProperty' ,
                 'functional'        : 'FunctionalProperty',
                 'inversefunctional' : 'InverseFunctionalProperty'}

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
    def serialize(self, encoding='utf-8'):
        return self.getDOM().toprettyxml(encoding=encoding)

    def generateClass(self, name, superclasses=[], labels=[], comments=[],
                      descriptions=[], classproperties=[]):
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
                               propertyproperties=[]):
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
    def __init__(self, file=None):
        # 'file' seems to be None only in tests
        OWLBase.__init__(self)

        if file is not None:
            self._dom = parse(file)

            if self._dom.doctype:
                self._dom.doctype.name = 'rdf:RDF'

            self.ensureEntities()

        self._keywords = {}
        self._relations = {}
        self._keyword_relationships = set()
        self._props = []
        self.ensureBuiltinProperties()

    def addKeyword(self, name, **kwargs):
        self._keywords.setdefault(name, {}).update(kwargs)

    def getKeywords(self):
        """ Yields dictionaries describing each keyword.
            Possible keys in the dictionary are: name, disambiguation
            and description.  The 'name' key is guarenteed to exist. """
        valid_keys = ['name', 'disambiguation', 'description']
        for (name, fields) in self._keywords.items():
            fields['name'] = name
            yield dict([p for p in fields.items() if p[0] in valid_keys])

    def getRelations(self):
        """ Yields dictionaries describing each relation.
            Possible keys in the dictionary are: name, description,
            types, inverse, weight. The 'name' key is guarenteed to exist. """
        valid_keys = ['name', 'description', 'types', 'inverse', 'weight']
        for (name, fields) in self._relations.items():
            fields['name'] = name
            yield dict([p for p in fields.items() if p[0] in valid_keys])

    def getKeywordRelationshps(self):
        """ Yields lists describing each keyword relationship.
            Each list will contain exactly (left, relation, right). """
        for triple in self._keyword_relationships:
            yield triple

    def addRelation(self, name, **kwargs):
        self._relations.setdefault(name, {}).update(kwargs)

    def addKeywordRelationship(self, left, name, right):
        self._keyword_relationships.add((left, name, right))

    def objectProperties(self):
        """Return known non builtin relations"""
        return self._props

    def getBuiltinProperties(self):
        return [ 'childOf', 'parentOf', 'synonymOf' ]

    def ensureBuiltinProperties(self):
        """Ensure existance of OWL built-in relations.

        rdfs:subClassOf     -- childOf <-> parentOf
        owl:equivalentClass -- synonymOf
        """

        self.addRelation(u'childOf', weight=1.0, types=[u'transitive'],
                         inverse=u'parentOf')

        self.addRelation(u'synonymOf', weight=1.0,
                            types=[u'transitive', u'symmetric'])

    def importProperties(self):
        for owlObjectProperty in self._dom.getElementsByTagName('owl:ObjectProperty'):
            self.importObjectProperty(owlObjectProperty)

    def importObjectProperty(self, prop):
        rid = prop.getAttribute('rdf:ID')

        if not rid: return

        if not rid in self.getBuiltinProperties():
            self._props.append(rid)

        owl_type = re.compile('^' + self._entities['owl'] + '(.*)Property$')
        types = []
        for type in prop.getElementsByTagName('rdf:type'):
            match = owl_type.search(type.getAttribute('rdf:resource'))
            if match:
                types.append(match.group(1).lower())

        inverses = []
        for inverse in prop.getElementsByTagName('owl:inverseOf'):
            inverses.append(parseURIRef(inverse.getAttribute('rdf:resource'))\
                            ['fragment'])

        if len(inverses) > 1:
            log.warning("Many inverses (%r) were found for relationship %s. "
                        "Only the first will be used."
                        %(inverses, rel.name))
        inverse = None
        if inverses and inverses[0]: inverse = inverses[0]

        weights = prop.getElementsByTagName('nip:weight')
        if weights and weights[0].firstChild:
            weight = float(weights[0].firstChild.data)
        else:
            weight = 1.0

        # Disabled: titles are used as names (FIXME)
        # labels = prop.getElementsByTagName("rdfs:label")
        # try:
        #     rel.setTitle(labels[0].firstChild.data)
        # except:
        #     rel.setTitle(rel.getId())

        descriptions = prop.getElementsByTagName("dc:description")
        try:
            description = descriptions[0].firstChild.data
        except:
            description = u''

        self.addRelation(rid, types=types, inverse=inverse,
                         weight=weight, description=description)

        # This is assuming that the domain and range are specified
        # in this sort of format:
        # <owl:ObjectProperty rdf:ID="awardedAt">
        #   <rdfs:range rdf:resource="#Festival"/>
        #   <rdfs:domain rdf:resource="#Award"/>
        # </owl:ObjectProperty>
        dr = map(prop.getElementsByTagName,
                 ('rdfs:domain', 'rdfs:range'))
        dr = [d and d[0].getAttribute('rdf:resource') for d in dr]
        if dr[0] and dr[1]:
            dr = [dr[0][1:], dr[1][1:]]
            map(self.addKeyword, dr)
            self.addKeywordRelationship(dr[0], rid, dr[1])

        return rid

    def importClasses(self):
        for owlClass in self._dom.getElementsByTagName('owl:Class'):
            self.importClass(owlClass)

    def importClass(self, cl):
        kid = cl.getAttribute('rdf:ID') or parseURIRef(cl.getAttribute('rdf:about'))['fragment']

        # After testing a few different ontologies found on the web,
        # it seems that this is required to make things work.
        if not kid: return

        #XXX: This is incorrect.  See #14.
        #for label in cl.getElementsByTagName('rdfs:label'):
        #    # ignore language and use value of first text or cdata node.
        #    if label.firstChild:
        #        title = label.firstChild.data.strip()
        #        if title: break

        description = u''
        for comment in cl.getElementsByTagName('rdfs:comment'):
            # ignore language and use value of first text or cdata node.
            if comment.firstChild:
                description = comment.firstChild.data.strip()
                if description: break

        #XXX: This is incorrect.  See #15.
        #for description in cl.getElementsByTagName('dc:description'):
        #    # ignore language and use value of first text or cdata node.
        #    if description.firstChild:
        #        description = description.firstChild.data.strip()
        #        if description: break

        self.addKeyword(kid, description=description)

        src = kid
        for equivalentClass in cl.getElementsByTagName('owl:equivalentClass'):
            dst = parseURIRef(equivalentClass.getAttribute('rdf:resource'))['fragment']
            self.addKeyword(dst)
            self.addKeywordRelationship(src, u'synonymOf', dst)

        for superclass in cl.getElementsByTagName('rdfs:subClassOf'):
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
                self.addKeyword(dst)
                self.addKeywordRelationship(src, u'childOf', dst)

        for classObjectProperty in self.objectProperties():
            for prop in cl.getElementsByTagName(classObjectProperty):
                dst = parseURIRef(prop.getAttribute('rdf:resource'))['fragment']
                self.addKeyword(dst)

                propName = prop.tagName
                self.addKeywordRelationship(src, propName, dst)

def exportOWL(ot):
    """ Export keyword structure to OWL. """
    exporter = OWLExporter()
    entities = exporter.getEntities()

    # Export OWL object properties.
    for rel in ot.queryRelations():
        exporter.generateObjectProperty(
                name = rel.name,
                types = [entities['owl'] + exporter.owl_types[t]
                         for t in rel.types],
                inverses = rel.inverse and [rel.inverse.name] or [],
                domains = [entities['owl'] + 'Class'],
                ranges = [entities['owl'] + 'Class'],
                labels = [],
                comments = [],
                descriptions = rel.description and [rel.description] or [],
                propertyproperties = [('nip:weight', str(rel.weight))]
        )

    # Export OWL classes.
    for kw in ot.queryKeywords():
        # XXX: Not 100% (or even really 50%) sure that this
        #      does the right thing...
        scs = [ kwr.left.name for kwr in kw.right_relations 
                                      if kwr.relation.name == 'childOf' ]
        # XXX: Not sure exactly what this does...
        ops = []
        # for r in keyword.getRelations():
        #     if p not in [ 'childOf', 'parentOf', 'synonymOf' ]:
        #         for c in keyword.getReferences(p):
        #             ops.append((p,c.getName()))
        ops = [("leftOPS", "rightOPS")]
        lang = 'en'
        label = kw.name
        comment = kw.disambiguation
        description = kw.description
        exporter.generateClass(
               name = kw.name,
               superclasses = scs,
               labels = [(lang, label)],
               comments = [(lang, comment)],
               descriptions = [(lang, description)],
               classproperties = ops
        )

        ecs = [ kwr.left.name for kwr in kw.right_relations
                                      if kwr.relation.name == 'synonymOf']
        ecs += [ kwr.right.name for kwr in kw.left_relations
                                        if kwr.relation.name == 'synonymOf']
        for c in ecs:
            exporter.generateEquivalentClass(kw.name, c)

        return exporter.serialize()

if __name__ == "__main__":
    # Code to import an ontology.
    from pyols.tests import setup_test_db
    from pyols.api import OntologyTool
    from pyols.db import db
    from pyols import graphviz
    from pyols.model import *

    setup_test_db()
    ot = OntologyTool(u"foo")
    oi = OWLImporter("./doc/beer.owl")
    oi.importClasses()
    oi.importProperties()

    for rel in oi.getRelations():
        ot.addRelation(**rel)

    for kw in oi.getKeywords():
        Keyword.new(namespace=ot._namespace, **kw).assert_valid()
    db.flush()

    for kwr in oi.getKeywordRelationshps():
        ot.addKeywordRelationship(*kwr)
    db.flush()

    open("/home/wolever/x.dot", "w").write(ot.generateDotSource())

    print exportOWL(ot)
