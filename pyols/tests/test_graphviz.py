from pyols.api import OntologyTool
from pyols.graphviz import DotTool #XXX: not used
from pyols.tests import run_tests, db

try:
    from pyols.tests.pydot import dot_parser
except ImportError:
    raise Exception("Graphviz tests can't be run without pyprocessing. If "
                    "you install pyOLS using `python setup.py develop` it "
                    "will be automatically installed for you.")

class TestDotTool:
    def setup(self):
        db().begin_txn()
        self.ot = OntologyTool('gv_test_ns')

    def teardown(self):
        db().abort_txn()

    def testSimpleGraph(self):
        for kw in ("kw0", "kw1", "kw2"):
            self.ot.addKeyword(kw)

        for rel in ("rel0", "rel1"):
            self.ot.addRelation(rel)

        db().flush()

        for kwr in (("kw0", "rel0", "kw1"),
                    ("kw0", "rel1", "kw2"),
                    ("kw2", "rel0", "kw0")):
            self.ot.addKeywordRelationship(*kwr)

        db().flush()

        dot = self.ot.generateDotSource()
        print dot
        1/0


run_tests()
