from Products.CMFCore.utils import UniqueObject 
from Products.CMFPlone.PloneFolder import PloneFolder
from Globals import InitializeClass, PersistentMapping
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from AccessControl.SecurityInfo import ClassSecurityInfo
from config import PROJECTNAME
import zLOG
import popen2
import os

from warnings import warn
from config import *

class GraphVizTool(UniqueObject, PloneFolder,
                         ActionProviderBase): 
    """A tool to provide graph rendering.

    Based on the GraphViz layout programs (http://www.graphviz.org)
    """

    id = 'graphviz_tool' 
    meta_type= 'GraphViz Tool'

    plone_tool = 1 

    security = ClassSecurityInfo()
    security.declareObjectPublic()

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

InitializeClass(GraphVizTool)
