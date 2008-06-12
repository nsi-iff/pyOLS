from Products.CMFCore.utils import UniqueObject 
from Products.CMFPlone.PloneFolder import PloneFolder
from Globals import InitializeClass, PersistentMapping
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from AccessControl.SecurityInfo import ClassSecurityInfo
from config import PROJECTNAME
import zLOG
import popen2

from warnings import warn
from config import *

class GraphVizTool(UniqueObject, PloneFolder,
                         ActionProviderBase): 
    """A tool to provide graph rendering.

    Based on the GraphViz layout programs (URL here)
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
        '''returns a list of the graphviz rendering tools'''
        return self._toollist

    def getLayouter(self):
        """Return the currently used GraphViz layouter"""
        return self._layouter

    def getTool(self):
        """Deprecated, use getLayouter"""
        warn("getTool() is deprecated. Please use getLayouter() instead.",
             DeprecationWarning)
        return self.getLayouter()

    def setLayouter(self, layouter='fdp'):
        """Set the currently used GraphViz layouter"""

        if not layouter in self._toollist:
            raise KeyError, "Layouter not known: %s. Please choose one of %s" % (layouter, self._toollist)
        else:
            self._layouter = layouter
        
    def setTool(self, tool='fdp'):
        """Deprecated, use setLayouter instead"""
        warn("setTool() is deprecated. Please use setLayouter() instead.",
             DeprecationWarning)
        self.setLayouter(tool)

    def renderGraph(self, graph, tool='', options=[]):
        """
        Renders the given graph. Returns file like object with result.
        Type is dependable on options.
        """
        if tool == '':
            tool = self.getLayouter()
        
        tool = os.path.join(GV_BIN_PATH, tool)

        options = " ".join(options)
        
        (pout,pin) = popen2.popen4(cmd = "%s %s" % (tool, options), mode = "b")
        pin.write(graph)
        pin.close()

        data = pout.read()
        pout.close()
        
        return data

InitializeClass(GraphVizTool)
