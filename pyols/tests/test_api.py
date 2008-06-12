from pyols.api import OntologyTool
from pyols.model import Keyword, Namespace
from pyols.tests import run_tests, reset_db
from pyols.exceptions import PyolsNotFound

from nose.tools import raises

class TestOntologyTool:
    def setup(self):
        # ot => OntologyTool
        self.ot = OntologyTool(u"testNS")

    def teardown(self):
        reset_db()

    def addKeyword(self, name=u"testKW", disambiguation=u"dis",
                   description=u"desc"):
        """ Add a keyword using a call to the OT. """
        self.ot.addKeyword(name, disambiguation, description)

    def getKeyword(self, name=u"testKW"):
        return self.ot.getKeyword(name)

    def checkKeyword(self, kw, name=u"testKW", disambiguation=u"dis",
                     description=u"desc"):
        assert kw
        assert kw.disambiguation == disambiguation
        assert kw.description == description
        assert kw.namespace.name == self.ot.namespace

    def keyword_new(self, name=u"testKW", disambiguation=u"dis",
                    description=u"desc"):
        """ Add a keyword using Keyword.new. """
        kw = Keyword.new(namespace=self.ot._namespace, name=name,
                         disambiguation=disambiguation,
                         description=description)
        kw.flush()

    def keyword_getby(self, name=u"testKW"):
        """ Query for a keyword using Keyword.get_by.
            Distinct from getKeyword, which makes a call to the OT. """
        return Keyword.get_by(name=name)

    def testAddKeyword(self):
        self.addKeyword()
        k = self.keyword_getby()
        self.checkKeyword(k)

    def testGetKeyword(self):
        self.keyword_new()
        k = self.getKeyword()
        self.checkKeyword(k)

    @raises(PyolsNotFound)
    def testGetInvalidKeyword(self):
        self.getKeyword(u"bad keyword")

    def testChangeNamespace(self):
        nn = u"newNamespace" # nn => newNamespace
        self.ot.namespace = nn
        assert Namespace.get_by(name=nn)
        assert self.ot.namespace == nn

        # Keywords added should be part of the new namespace
        self.addKeyword()
        k = self.keyword_getby()
        assert k.namespace.name == nn

        # And we should be able to go back to the old NS without an issue
        self.ot.namespace = u"testNS"
        assert self.ot.namespace == "testNS"


run_tests(__name__)
