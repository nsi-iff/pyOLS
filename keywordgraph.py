from Products.CMFCore.utils import getToolByName
from cStringIO import StringIO

def dotID(string):
    """Encode 'string' into a DOT ID usable inside double-quotes.

       DOT ID is "any double-quoted string ("...") possibly containing escaped quotes (\")",
       see <http://www.graphviz.org/doc/info/lang.html>.
    """
    return string.replace('"', '\\"')
    # .encode('unicode_escape', 'backslashreplace')

class KeywordGraph:
    """Dot code generator for keyword graphs.
    """

    def __init__(self, font='', relfont='', focus_nodeshape = 'ellipse', focus_nodecolor = '#dee7ec', focus_node_font_color = '#000000', focus_node_font_size = 9, first_nodeshape = 'box', first_nodecolor = '#dee7ec', first_node_font_color = '#000000', first_node_font_size = 8, second_nodeshape = 'box', second_nodecolor = '#dee7ec', second_node_font_color = '#000000', second_node_font_size = 7, edgeshape = 'normal', edgecolor = '#cde2a7', edge_font_color = '#000000', edge_font_size = 8):
        self._text = StringIO()
        self._font = font
        self._relfont = relfont
        self._focus_nodeshape = focus_nodeshape
        self._focus_nodecolor = focus_nodecolor
        self._focus_node_font_color = focus_node_font_color
        self._focus_node_font_size = focus_node_font_size
        self._first_nodeshape = first_nodeshape
        self._first_nodecolor = first_nodecolor
        self._first_node_font_color = first_node_font_color
        self._first_node_font_size = first_node_font_size
        self._second_nodeshape = second_nodeshape
        self._second_nodecolor = second_nodecolor
        self._second_node_font_color = second_node_font_color
        self._second_node_font_size = second_node_font_size
        self._edgeshape = edgeshape
        self._edgecolor = edgecolor
        self._edge_font_color = edge_font_color
        self._edge_font_size = edge_font_size

    def write(self, text):
        self._text.write(text)

    def getValue(self):
        return self._text.getvalue()
        # size="11,8"; w="5";
        #overlap="false";
        #splines="true";
        #len="10";
        #pack="false";
        #packMode="graph";
        #decorate="true";
        #labelfloat="false";
        #ranksep="equally";
        #rankdir="LR";
    def graphHeader(self, root):
        self._text.write('''digraph G{
        root="%s";
#        size="11,8";
#        len="10";
        pack="1";
        packmode="node";
        normalize="1";
        splines="polyline";
        concentrate="false";
        overlap="false";
        pack="false";
        node [color="#8cacbb", style="filled", shape="%s", fontname="%s", fillcolor="%s", fontcolor="%s", fontsize="%s"];
        edge [color="#8cacbb", shape="%s", fontname="%s", fillcolor="%s", fontcolor="%s", fontsize="%s"];
        ''' % (dotID(root.getName()), dotID(self._first_nodeshape), dotID(self._font), dotID(self._first_nodecolor), dotID(self._first_node_font_color), dotID(str(self._first_node_font_size)), dotID(self._edgeshape), dotID(self._relfont), dotID(self._edgecolor), dotID(self._edge_font_color), dotID(str(self._edge_font_size))))

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


    def firstLevelNode(self, node):
        nodelabel = node.getName()
        #cut long titles
        if len(nodelabel) > 15:
            nodelabel = nodelabel[0:13] + '...'

        desc = node.getKwDescription()
        if desc:
            tooltip = node.getName() + "&#13;&#10;" + desc
        else:
            tooltip = node.getName()

        self._text.write('"%s" [fontsize="%s", label="%s", URL="%s/keyword_context_view", tooltip="%s"];\n' % (dotID(node.getName()), dotID(str(self._focus_node_font_size)), dotID(nodelabel), dotID(node.absolute_url()), dotID(tooltip)))

    def secondLevelNode(self, node):
        nodelabel = node.getName()
        #cut long titles
        if len(nodelabel) > 10:
            nodelabel = nodelabel[0:8] + '...'

        desc = node.getKwDescription()
        if desc:
            tooltip = node.getName() + "&#13;&#10;" + desc
        else:
            tooltip = node.getName()

        self._text.write('"%s" [shape="%s", fillcolor="%s", fontcolor="%s", fontsize="%s", label="%s", URL="%s/keyword_context_view", tooltip="%s"];\n' % (dotID(node.getName()), dotID(self._second_nodeshape), dotID(self._second_nodecolor), dotID(self._second_node_font_color), dotID(str(self._second_node_font_size)), dotID(nodelabel), dotID(node.absolute_url()), dotID(tooltip), ))

    def relation(self, node, cnode, rel):
        self.write('"%s" -> "%s" [label="%s"];\n' % (dotID(node.getName()), dotID(cnode.getName()), dotID(rel)))
