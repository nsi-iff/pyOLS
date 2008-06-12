from Products.CMFCore.utils import getToolByName
from cStringIO import StringIO

def dotID(string):
    """Encode 'string' into a DOT ID usable inside double-quotes.

       DOT ID is "any double-quoted string ("...") possibly containing escaped quotes (\")",
       see <http://www.graphviz.org/doc/info/lang.html>.
    """
    return string.replace('"', '\\"').encode('unicode_escape', 'backslashreplace')

class KeywordGraph:
    """Dot code generator for keyword graphs.
    """

    def __init__(self, font, relfont):
        self._text = StringIO()
        self._font = font
        self._relfont = relfont

    def write(self, text):
        self._text.write(text)

    def getValue(self):
        return self._text.getvalue()

    def graphHeader(self, root):
        self._text.write('''digraph G{
        size="11,8";
        ranksep="1.5";
        rankdir="LR";
        len="10";
        w="5";
        root="%s";
        overlap="true";
        splines="true";
        node [shape="box", style="filled", fontname="%s"];
        edge [fontsize="7", fontcolor="#cccccc", fontname="%s"];
        ''' % (dotID(root.getName()), dotID(self._font), dotID(self._relfont)))

    def graphFooter(self):
        self._text.write("}\n")

    def focusNode(self, node):
        self._text.write('"%s" [fillcolor="#ff999999", fontsize="11", label="%s", shape="ellipse"];\n' % (dotID(node.getName()), dotID(node.title_or_id())))


    def firstLevelNode(self, node):
        nodelabel = node.title_or_id()
        #cut long titles
        if len(nodelabel) > 20:
            nodelabel = nodelabel[0:18] + '...'

        desc = node.getKwDescription()
        if desc:
            tooltip = node.title_or_id() + r"\n\n" + desc
        else:
            tooltip = node.title_or_id()

        self._text.write('"%s" [fontsize="9", fillcolor="#ffcccc", label="%s", URL="%s/keyword_context_view", tooltip="%s"];\n' % (dotID(node.getName()), dotID(nodelabel), dotID(node.absolute_url()), dotID(tooltip)))

    def secondLevelNode(self, node):
        nodelabel = node.title_or_id()
        #cut long titles
        if len(nodelabel) > 10:
            nodelabel = nodelabel[0:8] + '...'

        desc = node.getKwDescription()
        if desc:
            tooltip = node.title_or_id() + r"\n\n" + desc
        else:
            tooltip = node.title_or_id()

        self._text.write('"%s" [fontsize="9", fillcolor="#fff0f0", label="%s", URL="%s/keyword_context_view", tooltip="%s"];\n' % (dotID(node.getName()), dotID(nodelabel), dotID(node.absolute_url()), dotID(tooltip)))

    def relation(self, node, cnode, rel):
        self.write('"%s" -> "%s" [label="%s"];\n' % (dotID(node.getName()), dotID(cnode.getName()), dotID(rel)))
