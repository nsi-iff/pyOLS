"""Graphviz related functions.
There is still some PloneOntology code in here, so be warned!"""
import popen2
import os
from cStringIO import StringIO

from pyols.api import publish
from pyols.exceptions import PyolsValidationError, PyolsEnvironmentError
from pyols.config import config
from pyols.util import binary

class GraphvizTool: 
    """ A tool to provide graph rendering.
        Based on the Graphviz layout programs (http://www.graphviz.org) """

    engine_list = ('dot','twopi','neato','fdp','circo')

    def __init__(self, layout_engine='dot'):
        """ Initialize the GVTool with the default engine.
            An exception will be raised if the tool is not in the engine_list:
            >>> v = GraphvizTool('neato')
            >>> v = GraphvizTool('bad_engine')
            Traceback (most recent call last):
              ...
            PyolsValidationError: Invalid layout engine: bad_engine
            >>> """
        if layout_engine not in self.engine_list:
            raise PyolsValidationError("Invalid layout engine: " + layout_engine)
        self._layouter = layout_engine

    def assertLayouterPresent(self, layouter=None):
        """ Check if current or specified layouter is present on the system.
            If it is not found, raise an exception.
            >>> config['graphviz_path'] = '/bin/'
            >>> v = GraphvizTool()
            >>> v.assertLayouterPresent('sh')
            >>> v.assertLayouterPresent('bad_engine')
            Traceback (most recent call last):
              ...
            PyolsEnvironmentError: Layout engine '/bin/bad_engine' not found
            >>> """

        if layouter is None:
            layouter = self._layouter

        layouter = os.path.join(config['graphviz_path'], layouter)
        if not os.path.exists(layouter):
            raise PyolsEnvironmentError("Layout engine %r not found" %layouter)

    def renderGraph(self, graph):
        """ Render 'graph'.
            If there is error text, an exception is raised.  Otherwise
            the rendered PNG is returned. """

        self.assertLayouterPresent()

        tool = os.path.join(config['graphviz_path'], self._layouter)

        # 2006-08-03 Seperate streams for output and error.
        #            Avoids problems with fonts not found.
        cmd = "%s -Tpng" %(tool)
        (pout, pin, perr) = popen2.popen3(cmd=cmd, mode="b")
        pin.write(graph)
        pin.close()

        data  = pout.read()
        pout.close()
        error = perr.read()
        perr.close()

        if error:
            raise PyolsEnvironmentError("The command %r produced text on "
                                        "stderr: %s" %(cmd, error))

        return data


def dotID(string):
    """ Encode 'string' into a DOT ID usable inside double-quotes.
        A DOT ID is "any double-quoted string ("...") possibly containing
        escaped quotes (\")".
        >>> print dotID('ab"c"')
        ab\\"c\\"
        >>> print dotID('sp\\\\am')
        sp\\\\am
        >>> print dotID('ab\\ncd')
        ab\\ncd
        >>>
        See <http://www.graphviz.org/doc/info/lang.html>.  """
        # Ug, doctests aren't great for showing how the escaping is
        # dealt with.  Basically, newlines and "\" are escaped.
    return string.replace("\\", r"\\").replace('"', r'\"').replace("\n", r"\n")

class DotOptionsDict(dict):
    """ A dict which will escape each item with dotID before returning it.
        >>> f = DotOptionsDict()
        >>> f['spam'] = 'a "quoted" string'
        >>> print f['spam']
        a \\"quoted\\" string
        >>> f['ham'] = 42
        >>> f['ham']
        u'42'
        >>> """
    def __getitem__(self, item):
        # Note: wrapping in unicode is important incase the
        #       item is something un-stringy (like an int).
        #       It is _not_ intended to decode an encoded str.
        return dotID(unicode(dict.__getitem__(self, item)))

class DotTool:
    """ Dot code generator for keyword graphs. """
    default_options = {
        'root_name': '',
        'font': '',
        'relfont': '',
        'focus_nodeshape': 'ellipse',
        'focus_nodecolor':  '#dee7ec',
        'focus_node_font_color': '#000000',
        'focus_node_font_size':  9,
        'first_nodeshape':  'box',
        'first_nodecolor':  '#dee7ec',
        'first_node_font_color':  '#000000',
        'first_node_font_size':  8,
        'second_nodeshape':  'box',
        'second_nodecolor':  '#dee7ec',
        'second_node_font_color': '#000000',
        'second_node_font_size':  7,
        'edgeshape':  'normal',
        'edgecolor':  '#cde2a7',
        'edge_font_color':  '#000000',
        'edge_font_size':  8
    }

    def __init__(self, **options):
        self._text = StringIO()
        # Implicit in this call is a copy of default_options
        self._options = DotOptionsDict(self.default_options.items())
        self._options.update(options)

        if len(self._options) != len(self.default_options):
            invalid_options = set(self.default_options.keys()) \
                              - set(options.items())
            raise TypeError("Unexpected options passed to __init__: %s"\
                            %(", ".join(map(str, invalid_options))))
        self.graphHeader()

    def _truncate(self, s):
        """ Truncate string 's' to 30 characters.
            >>> d = DotTool()
            >>> d._truncate("short")
            'short'
            >>> d._truncate("123"*10)
            '123123123123123123123123123123'
            >>> d._truncate("123"*11)
            '123123123123123123123123123...'
            >>> """
        # Note: The 'n' is hard-coded because bad things happen when truncation
        #       is done to different lengths (for example, there may be a
        #       node defined by firstLevelNode having a lenght of 30, but
        #       it may be referenced later having a different length, creating
        #       two nodes in the graph.
        n = 30
        if len(s) > n:
            s = s[0:n-3] + '...'
        return s

    def write(self, text):
        self._text.write(text)

    def getSource(self):
        """ Get the source for the current graph. """
        self.graphFooter()
        return self._text.getvalue()

    def graphHeader(self):
        self._text.write('''digraph G {
        root="%(root_name)s";
        //size="11,8";
        //len="10";
        pack="1";
        packmode="node";
        normalize="1";
        splines="polyline";
        concentrate="false";
        overlap="false";
        pack="false";
        node [color="#8cacbb", style="filled", shape="%(first_nodeshape)s", 
              fontname="%(font)s", fillcolor="%(first_nodecolor)s",
              fontcolor="%(first_node_font_color)s",
              fontsize="%(first_node_font_size)s"];
        edge [color="#8cacbb", shape="%(edgeshape)s", fontname="%(relfont)s",
              fillcolor="%(edgecolor)s", fontcolor="%(edge_font_color)s",
              fontsize="%(edge_font_size)s"];
        ''' % (self._options))

    def graphFooter(self):
        self._text.write("}\n")

    def focusNode(self, node):
        nodelabel = node.getName()
        #cut long titles
        if len(nodelabel) > 20:
            nodelabel = nodelabel[0:18] + '...'

        desc = node.getKwDescription()
        if desc:
            tooltip = node.getName() + "&#13;&#10;" + desc
        else:
            tooltip = node.getName()

        self._text.write('"%s" [shape="%s", fillcolor="%s", fontcolor="%s", fontsize="%s", label="%s", tooltip="%s"];\n' % (dotID(node.getName()), dotID(self._focus_nodeshape), dotID(self._focus_nodecolor), dotID(self._focus_node_font_color), dotID(str(self._focus_node_font_size)), dotID(nodelabel), dotID(tooltip)))

    def firstLevelNode(self, name, description):
        name = self._truncate(name)

        self.write('"%s" [fontsize="%s", tooltip="%s"];\n'
                   %(dotID(name), self._options['focus_node_font_size'],
                     dotID(description)))

    def secondLevelNode(self, node):
        nodelabel = node.getName()
        # Truncate long names
        if len(nodelabel) > 10:
            nodelabel = nodelabel[0:8] + '...'

        desc = node.getKwDescription()
        if desc:
            tooltip = node.getName() + "&#13;&#10;" + desc
        else:
            tooltip = node.getName()

        self.write('"%s" [shape="%s", fillcolor="%s", fontcolor="%s", fontsize="%s", label="%s", URL="%s/keyword_context_view", tooltip="%s"];\n' % (dotID(node.getName()), dotID(self._second_nodeshape), dotID(self._second_nodecolor), dotID(self._second_node_font_color), dotID(str(self._second_node_font_size)), dotID(nodelabel), dotID(node.absolute_url()), dotID(tooltip), ))

    def relation(self, name, relation, child):
        """ Add a relation from name, through relation, to child. """
        (name, relation, child) = map(self._truncate, (name, relation, child))
        self.write('"%s" -> "%s" [label="%s"];\n'
                   %(dotID(name), dotID(child), dotID(relation)))

@staticmethod
@publish
def getGraphvizNodeshapes():
    """ Returns a list of possible node shapes. """
    return ['box', 'polygon', 'ellipse', 'circle', 'point',
            'egg', 'triangle', 'plaintext', 'diamond', 'trapezium',
            'parallelogram', 'house', 'pentagon', 'hexagon', 'septagon',
            'octagon', 'doublecircle', 'doubleoctagon', 'tripleoctagon',
            'invtriangle', 'invtrapezium', 'invhouse', 'Mdiamond',
            'Msquare', 'Mcircle', 'rect', 'rectangle', 'none']

@staticmethod
@publish
def getGraphvizEdgeShapes():
    """ Returns a list of possible edge shapes. """
    return ['box', 'crow', 'diamond', 'dot', 'inv', 'none',
            'normal', 'tee', 'vee']

@publish
def getOntologyGraph(ot, options={}):
    """ Graphs the output of getOntologyDotSource and returns a
        PNG image containing the output.
        'options' is a dictionary which will be passed to getOntologyDotSource.
        It can also contain 'layout_engine', the layout enginge which will be
        used to generate the graph.  The default is 'dot', and the possible
        engines are: """ + ", ".join(GraphvizTool.engine_list)
    engine = options.setdefault('layout_engine', 'dot')
    # Delete the option so it doesn't get passed to getOntologyDotSource
    del options['layout_engine']
    graph = getOntologyDotSource(ot, options)
    
    t = GraphvizTool(layout_engine=engine)
    graph = t.renderGraph(graph)
    return binary(graph)

@publish
def getOntologyDotSource(ot, options={}):
    """ Generate dot source code for a graph of all the keywords in the
        current namespace and their relationships.
        'options' is a dictionary which can contain:\n        """ + \
        "\n        ".join(["%s: %s"%i for i in DotTool.default_options.items()
                          if i[0] != 'root_name'])

    dot = DotTool(root_name="", **options)

    for kw in ot.queryKeywords():
        dot.firstLevelNode(kw.name, kw.description)

    for rel in ot.queryKeywordRelationships():
        dot.relation(rel.left.name, rel.relation.name, rel.right.name)

    return dot.getSource()

from pyols.tests import run_doctests
run_doctests()
