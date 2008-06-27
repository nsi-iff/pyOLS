from pyols.api import OntologyTool
from pyols.tests import run_tests, db, PyolsDBTest

try:
    from pyols.tests.pydot import dot_parser, pydot
except ImportError:
    raise Exception("Graphviz tests can't be run without pyprocessing. If "
                    "you install pyOLS using `python setup.py develop` it "
                    "will be automatically installed for you.")


from nose.tools import assert_equal, assert_raises
import difflib

# The default skeleton graph, used by GraphChecker.
default_graph = """
digraph G {
        root="";
        pack="1";
        packmode="node";
        normalize="1";
        splines="polyline";
        concentrate="false";
        overlap="false";
        pack="false";
        node [color="#8cacbb", style="filled", shape="box", 
              fontname="", fillcolor="#dee7ec",
              fontcolor="#000000",
              fontsize="8"];
        edge [color="#8cacbb", shape="normal", fontname="",
              fillcolor="#cde2a7", fontcolor="#000000",
              fontsize="8"];
}
"""

def qt(s):
    """ A little helper function which will wrap strings in quotes
        to make the output of pydot and graphviz.py the same. """
    if isinstance(s, basestring):
        return '"' + s + '"'
    if isinstance(s, dict):
        return dict([(key, qt(val)) for (key, val) in s.items()])

class GraphChecker:
    """ A class which will generate a graph which can be used to verify
        that the output of the graphviz tool is correct.
        It's interface is designed to mirror the interface of OntologyTool. """
    def __init__(self):
        self._graph = dot_parser.parse_dot_data(default_graph)

    def addKeyword(self, kw):
        options = {'fontsize': '9', 'tooltip': ''} 
        node = pydot.Node(qt(kw), **qt(options))
        self._graph.add_node(node)

    def addKeywordRelationship(self, left, relation, right):
        edge = pydot.Edge(src=qt(left), dst=qt(right))
        edge.set_label(qt(relation))
        self._graph.add_edge(edge)

    def toString(self):
        """ Return a string representation of the graph.
            Probably helpful for debugging. """
        return self._graph.to_string()

    def checkDot(self, dot):
        """ Verify that 'dot' contains the correct data. """
        new = dot_parser.parse_dot_data(dot)
        correct = self._graph.obj_dict

        print "--- CORRECT ---"
        print self.toString()
        print "--- ACTUAL ---"
        print new.to_string()

        new = new.obj_dict
        r = self._check_dict(new['attributes'], correct['attributes'])
        if r: raise AssertionError("In graph attributes: %s" %(r,))

        for key in ('nodes', 'edges'):
            for node in correct[key]:
                if node not in new[key]:
                    raise AssertionError("%s %s not in new." %(key, node))

                r = self._check_dict(correct[key][node][0],
                                     new[key][node][0])
                if r: raise AssertionError("%s %s differs: %s" %(key, node, r))
            r = self._missing_items(new[key], correct[key])
            if r: raise AssertionError("%s %s" %(key, r))

        for key in ('type', 'name', 'subgraphs'):
            assert_equal(new.get(key), correct.get(key))

    def _check_dict(self, new, correct):
        ignore = ('parent_graph', 'sequence')
        for key in correct:
            if key in ignore: continue
            if key not in new:
                return "%s not in new." %(key, )
            if new[key] != correct[key]:
                return "%r (new[%r]) != %r (correct[%r])"\
                       %(new[key], key, correct[key], key)
        return self._missing_items(correct, new)

    def _missing_items(self, correct, new):
        all = set(new).union(set(correct))
        missing_in_new = all - set(correct)
        missing_in_correct = all - set(new)
        if missing_in_correct:
            return "[%s] are in new but not correct."\
                    %(", ".join([repr(x) for x in missing_in_correct]))
        if missing_in_new:
            return "[%s] are in correct but not in new."\
                    %(", ".join([repr(x) for x in missing_in_new]))
        return None

class TestGraphChecker:
    def setup(self):
        self.gc0 = GraphChecker()
        self.gc1 = GraphChecker()

    def testMissing(self):
        def assert_both_fail():
            assert_raises(AssertionError, self.gc1.checkDot, self.gc0.toString())
            assert_raises(AssertionError, self.gc0.checkDot, self.gc1.toString())

        self.gc1.addKeyword("foo")
        assert_both_fail()

        self.gc0.addKeyword("foo")
        self.gc0.addKeywordRelationship("foo", "bar", "baz")
        assert_both_fail()

        self.gc0.addKeyword("blam")
        self.gc1.addKeyword("baz")
        assert_both_fail()

        # After putting all this back in everything should work
        self.gc0.addKeyword("baz")
        self.gc1.addKeyword("blam")
        self.gc1.addKeywordRelationship("foo", "bar", "baz")
        self.gc1.checkDot(self.gc0.toString())
        self.gc0.checkDot(self.gc1.toString())


class TestDotTool(PyolsDBTest):
    def setup(self):
        super(TestDotTool, self).setup()
        self.ot = OntologyTool(u'gv_test_ns')
        self.gc = GraphChecker()

    def testSimpleGraph(self):
        for kw in (u"kw0", u"kw1", u"kw2"):
            self.ot.addKeyword(kw)
            self.gc.addKeyword(kw)

        for rel in (u"rel0", u"rel1"):
            self.ot.addRelation(rel)

        db.flush()

        for kwr in ((u"kw0", u"rel0", u"kw1"),
                    (u"kw0", u"rel1", u"kw2"),
                    (u"kw2", u"rel0", u"kw0")):
            self.ot.addKeywordRelationship(*kwr)
            self.gc.addKeywordRelationship(*kwr)

        db.flush()

        dot = self.ot.getDotSource()
        self.gc.checkDot(dot)

    def testLongNames(self):
        long = u'this string has more than 30 characters'
        long_trunc = long[:27] + '...'
        short = u'this string has exactly 26'

        self.ot.addKeyword(long)
        self.gc.addKeyword(long_trunc)
        self.ot.addKeyword(short)
        self.gc.addKeyword(short)

        self.ot.addRelation(long)
        self.ot.addRelation(short)

        db.flush()

        self.ot.addKeywordRelationship(long, long, long)
        self.gc.addKeywordRelationship(long_trunc, long_trunc, long_trunc)

        self.ot.addKeywordRelationship(short, short, short)
        self.gc.addKeywordRelationship(short, short, short)

        self.ot.addKeywordRelationship(long, short, short)
        self.gc.addKeywordRelationship(long_trunc, short, short)

        self.ot.addKeywordRelationship(short, long, short)
        self.gc.addKeywordRelationship(short, long_trunc, short)

        db.flush()
        dot = self.ot.getDotSource()
        self.gc.checkDot(dot)

run_tests()
