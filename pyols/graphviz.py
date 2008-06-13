import popen2
import os

from warnings import warn
from pyols.api import publish

from cStringIO import StringIO

class GraphVizTool: 
    """ A tool to provide graph rendering.
        Based on the GraphViz layout programs (http://www.graphviz.org) """

    _toollist = ('dot','twopi','neato','fdp','circo')

    def __init__(self):
        self._layouter = 'fdp'

    def toollist(self):
        """returns a list of the graphviz rendering tools.
        """
        return self._toollist

    def getLayouter(self):
        """Return the currently used GraphViz layouter.
        """
        return self._layouter

    def getTool(self):
        """Deprecated, use getLayouter.
        """
        warn("getTool() is deprecated. Please use getLayouter() instead.",
             DeprecationWarning)
        return self.getLayouter()

    def setLayouter(self, layouter='fdp'):
        """Set the currently used GraphViz layouter.
        """

        if not layouter in self._toollist:
            raise KeyError, "Layouter not known: %s. Please choose one of %s" % (layouter, self._toollist)
        else:
            self._layouter = layouter

    def setTool(self, tool='fdp'):
        """Deprecated, use setLayouter instead.
        """
        warn("setTool() is deprecated. Please use setLayouter() instead.",
             DeprecationWarning)
        self.setLayouter(tool)

    def isLayouterPresent(self, layouter=""):
        """Check if current or specified layouter is present on the system.
        """

        if not layouter:
            layouter = self.getLayouter()

        layouter = os.path.join(GV_BIN_PATH, layouter)

        (pout,pin) = popen2.popen4(cmd = "%s -V" % layouter)
        pin.close()
        output = pout.read()
        pout.close()

        return "version" in output

    def renderGraph(self, graph, tool='', options=[]):
        """Renders the given graph.

        Returns file like object with result which type is dependable on options and an error string, empty if none.
        """
        if not tool:
            tool = self.getLayouter()

        tool = os.path.join(GV_BIN_PATH, tool)

        options = " ".join(options)

        # 2006-08-03 Seperate streams for output and error. Avoids problems with fonts not found.
        (pout, pin, perr) = popen2.popen3(cmd = "%s %s" % (tool, options), mode = "b")
        pin.write(graph)
        pin.close()

        data  = pout.read()
        pout.close()
        error = perr.read()
        perr.close()

        return (data, error)


def dotID(string):
    """ Encode 'string' into a DOT ID usable inside double-quotes.
        A DOT ID is "any double-quoted string ("...") possibly containing
        escaped quotes (\")".
        >>> print dotID('ab"c"')
        ab\\"c\\"
        >>> dotID('spam')
        'spam'
        >>>
        See <http://www.graphviz.org/doc/info/lang.html>.  """
    return string.replace('"', r'\"')

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
    """Dot code generator for keyword graphs.
    """
    default_options = {
        'header_name': '',
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

    def write(self, text):
        self._text.write(text)

    def getSource(self):
        """ Get the source for the current graph. """
        self.graphFooter()
        return self._text.getvalue()

    def graphHeader(self):
        self._text.write('''digraph G {
        root="%(header_name)s";
        #size="11,8";
        #len="10";
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
        # Truncate long names
        if len(name) > 15:
            name = name[0:13] + '...'

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
def getGraphvizEdgeShapesList():
    """ Returns a list of possible edge shapes. """
    return ['box', 'crow', 'diamond', 'dot', 'inv', 'none',
            'normal', 'tee', 'vee']

@publish
def generateDotSource(ot, **options):
    """ Generate dot source code for a graph of all the keywords in the
        current namespace and their relationships.
        Options are:\n""" + \
        "\n".join(["%s: %s"%i for i in DotTool.default_options.items()
                   if i[0] != 'header_name'])

    dot = DotTool(header_name="What's This?", **options)

    for kw in ot.queryKeywords():
        dot.firstLevelNode(kw.name, kw.description)

    for rel in ot.queryKeywordRelationships():
        dot.relation(rel.left.name, rel.relation.name, rel.right.name)

    return dot.getSource()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
