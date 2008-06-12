from Products.CMFCore.utils import getToolByName, UniqueObject
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl import getSecurityManager, Unauthorized
from Acquisition import aq_base, aq_inner, aq_parent
from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass, PersistentMapping

from keywordgraph import KeywordGraph
from keyword import Keyword
from ontology import Ontology
from utils import generateUniqueId
from config import *
import owl

from Products.Relations import interfaces
from Products.Relations.processor import process
from Products.Relations.exception import ValidationException
from zExceptions import NotFound

import zExceptions, zLOG
import difflib

from types import *

import os.path, sys, os, glob, re

from warnings import warn

def _unifyRawResults(results):
    """unify result list and add scores for unique objects.

    results is list of tuples (score, object).
    """

    result = []
    obs = []
    for c in results:
        if not c[1] in obs:
            result.append(c)
            obs.append(c[1])
        else:
            index = obs.index(c[1])
            result[index] = (result[index][0] + c[0], result[index][1])

    return result

#ALTERNATIVE unify with help of dict
##         kws = {}
##         for c in children:
##             if not kws.has_key(c[1].id):
##                 kws[c[1].id] = cExcept
##             else:
##                 kws[c[1].id] = (kws[c[1].id][0] + c[0], kws[c[1].id][1])

##         children = kws.values()

###the following code has been taken from TTF Query from Michael C. Fletcher to find Windows Fonts for the GV output.
###for Linux Fonts fc-list is used before we use this code
###ToDO: include copyright notice
"""Find system fonts (only works on Linux and Win32 at the moment)"""

def win32FontDirectory( ):
	"""Get User-specific font directory on Win32"""
	try:
		import _winreg
	except ImportError:
		return os.path.join(os.environ['WINDIR'], 'Fonts')
	else:
		k = _winreg.OpenKey(
			_winreg.HKEY_CURRENT_USER,
			r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
		)
		try:
			# should check that k is valid? How?
			return _winreg.QueryValueEx( k, "Fonts" )[0]
		finally:
			_winreg.CloseKey( k )

def win32InstalledFonts( fontDirectory = None ):
	"""Get list of explicitly *installed* font names"""
	import _winreg
	if fontDirectory is None:
		fontDirectory = win32FontDirectory()
	k = None
	items = {}
	for keyName in (
		r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
		r"SOFTWARE\Microsoft\Windows\CurrentVersion\Fonts",
	):
		try:
			k = _winreg.OpenKey(
				_winreg.HKEY_LOCAL_MACHINE,
				keyName
			)
		except OSError, err:
			pass
	if not k:
		# couldn't open either WinNT or Win98 key???
		return glob.glob( os.path.join(fontDirectory, '*.ttf'))
	try:
		# should check that k is valid? How?
		for index in range( _winreg.QueryInfoKey(k)[1]):
			key,value,_ = _winreg.EnumValue( k, index )
			if not os.path.dirname( value ):
				value = os.path.join( fontDirectory, value )
			value = os.path.abspath( value ).lower()
			if value[-4:] == '.ttf':
				items[ value ] = 1
		return items.keys()
	finally:
		_winreg.CloseKey( k )
	

def linuxFontDirectories( ):
	"""Get system font directories on Linux/Unix
	
	Uses /usr/sbin/chkfontpath to get the list
	of system-font directories, note that many
	of these will *not* be truetype font directories.

	If /usr/sbin/chkfontpath isn't available, uses
	returns a set of common Linux/Unix paths
	"""
	executable = '/usr/sbin/chkfontpath'
	if os.path.isfile( executable ):
		data = os.popen( executable ).readlines()
		match = re.compile( '\d+: (.+)')
		set = []
		for line in data:
			result = match.match( line )
			if result:
				set.append(result.group(1))
		return set
	else:
		directories = [
			# what seems to be the standard installation point
			"/usr/X11R6/lib/X11/fonts/TTF/",
			"/usr/share/X11/fonts/TTF/",
			# common application, not really useful
			"/usr/lib/openoffice/share/fonts/truetype/",
			"/usr/lib/openoffice.org2.0/share/fonts/truetype/",
			# documented as a good place to install new fonts...
			"/usr/share/fonts",
			# okay, now the OS X variants...
			"~/Library/Fonts/",
			"/Library/Fonts/",
			"/Network/Library/Fonts/",
			"/System/Library/Fonts/",
			"System Folder:Fonts:",
		]
		
		set = []
		def add( arg, directory, files):
			set.append( directory )
		for directory in directories:
			try:
				if os.path.isdir( directory ):
					os.path.walk(directory, add, ())
			except (IOError, OSError, TypeError, ValueError):
				pass
		return set

def findFonts(paths = None):
	"""Find fonts in paths, or the system paths if not given

	XXX Doesn't current support OS-X system paths
	"""
	files = {}
	if paths is None:
		if sys.platform == 'win32':
			fontDirectory = win32FontDirectory()
			paths = [
				fontDirectory,
			]
			# now get all installed fonts directly...
			for f in win32InstalledFonts(fontDirectory):
				# yes, it's inefficient, the interface
				# for win32InstalledFonts really should be
				# using sets, not lists
				files[f] = 1
		else:
			paths = linuxFontDirectories()
	elif isinstance( paths, (str, unicode)):
		paths = [paths]
	for path in paths:
		for file in glob.glob( os.path.join(path, '*.ttf')):
			files[os.path.abspath(file)] = 1
	return files.keys()

###
###
###END TTFQuery

class ClassificationTool(UniqueObject,
                         SimpleItem,
                         ActionProviderBase):
    """A tool to handle content syndication with keywords.
    """

    id = 'portal_classification'
    meta_type= 'Classification Tool'
    plone_tool = 1

    security = ClassSecurityInfo()
    #XXX proper security declarations
    security.declareObjectPublic()

    def __init__(self):
        self._fontpath=''
        self._fonts=[]
        data = os.popen('fc-list').readlines()
        if data != []:
         for el in data:
          self._fonts.append(el.split(":style")[0])
        else:
         for el in findFonts():
          if "\\" in el:
           self._fonts.append(el.split("\\")[len(el.split("\\"))-1][:-4])
          elif "/" in el:
           self._fonts.append(el.split("/")[len(el.split("/"))-1][:-4])
        self._fonts.sort()
        self.relevance_factors = PersistentMapping()
        self._cutoff = 0.1
        self._use_gv_tool = 0
        self._storage = 'kw_storage'
        self._classifytypes = []
        self._gvfont = ''
        self._relfont = ''
        self._forth = '1'
        self._back = '0'
        self._nodeshapes = ['box', 'polygon', 'ellipse', 'circle', 'point', 'egg', 'triangle', 'plaintext', 'diamond', 'trapezium', 'parallelogram', 'house', 'pentagon', 'hexagon', 'septagon', 'octagon', 'doublecircle', 'doubleoctagon', 'tripleoctagon', 'invtriangle', 'invtrapezium', 'invhouse', 'Mdiamond', 'Msquare', 'Mcircle', 'rect', 'rectangle', 'none']
        self._edgeshapes = ['box', 'crow', 'diamond', 'dot', 'inv', 'none', 'normal', 'tee', 'vee']
        self._focus_nodeshape = 'ellipse'
        self._focus_nodecolor = '#dee7ec'
        self._focus_node_font_color = '#000000'
        self._focus_node_font_size = 9
        self._first_nodeshape = 'box'
        self._first_nodecolor = '#dee7ec'
        self._first_node_font_color = '#000000'
        self._first_node_font_size = 8
        self._second_nodeshape = 'box'
        self._second_nodecolor = '#dee7ec'
        self._second_node_font_color = '#000000'
        self._second_node_font_size = 7
        self._edgeshape = 'normal'
        self._edgecolor = '#cde2a7'
        self._edge_font_color = '#000000'
        self._edge_font_size = 8
        self._encoding = 'utf-8'
        self._classifyRelationship = "classifiedAs_byPloneOntology"

    def getGVNodeShapesList(self):
        """Return the gv node shape list.
        """
        return self._nodeshapes

    def getGVEdgeShapesList(self):
        """Return the gv edge shape list.
        """
        return self._edgeshapes
    def getFocusNodeShape(self):
        """Return the current gv focus_nodeshape.
        """
        return self._focus_nodeshape

    def setFocusNodeShape(self, focus_nodeshape):
        """Set the focus_nodeshape for gv output.
        """
        self._focus_nodeshape=focus_nodeshape

    def getFocusNodeColor(self):
        """Return the current gv focus_nodecolor.
        """
        return self._focus_nodecolor

    def setFocusNodeColor(self, focus_nodecolor):
        """Set the focus_nodecolor for gv output.
        """
        self._focus_nodecolor=focus_nodecolor

    def getFocusNodeFontColor(self):
        """Return the current gv focus_node_font_color.
        """
        return self._focus_node_font_color

    def setFocusNodeFontColor(self, focus_node_font_color):
        """Set the focus_node_font_color for gv output.
        """
        self._focus_node_font_color=focus_node_font_color

    def getFocusNodeFontColor(self):
        """Return the current gv focus_node_font_color.
        """
        return self._focus_node_font_color

    def setFocusNodeFontColor(self, focus_node_font_color):
        """Set the focus_node_font_color for gv output.
        """
        self._focus_node_font_color=focus_node_font_color

    def getFocusNodeFontSize(self):
        """Return the current gv focus_node_font_size.
        """
        return self._focus_node_font_size

    def setFocusNodeFontSize(self, focus_node_font_size):
        """Set the focus_node_font_size for gv output.
        """
        self._focus_node_font_size=focus_node_font_size

    def getFocusNodeShape(self):
        """Return the current gv focus_nodeshape.
        """
        return self._focus_nodeshape

    def setFocusNodeColor(self, focus_nodeshape):
        """Set the focus_nodeshape for gv output.
        """
        self._focus_nodeshape=focus_nodeshape

    def getFocusNodeColor(self):
        """Return the current gv focus_nodecolor.
        """
        return self._focus_nodecolor

    def setFocusNodeColor(self, focus_nodecolor):
        """Set the focus_nodecolor for gv output.
        """
        self._focus_nodecolor=focus_nodecolor

    def getFocusNodeFontColor(self):
        """Return the current gv focus_node_font_color.
        """
        return self._focus_node_font_color

    def setFocusNodeFontColor(self, focus_node_font_color):
        """Set the focus_node_font_color for gv output.
        """
        self._focus_node_font_color=focus_node_font_color

    def getFocusNodeFontColor(self):
        """Return the current gv focus_node_font_color.
        """
        return self._focus_node_font_color

    def setFocusNodeFontColor(self, focus_node_font_color):
        """Set the focus_node_font_color for gv output.
        """
        self._focus_node_font_color=focus_node_font_color

    def getFocusNodeFontSize(self):
        """Return the current gv focus_node_font_size.
        """
        return self._focus_node_font_size

    def setFocusNodeFontSize(self, focus_node_font_size):
        """Set the focus_node_font_size for gv output.
        """
        self._focus_node_font_size=focus_node_font_size

    def getFirstNodeShape(self):
        """Return the current gv first_nodeshape.
        """
        return self._first_nodeshape

    def setFirstNodeShape(self, first_nodeshape):
        """Set the first_nodeshape for gv output.
        """
        self._first_nodeshape=first_nodeshape

    def getFirstNodeColor(self):
        """Return the current gv first_nodecolor.
        """
        return self._first_nodecolor

    def setFirstNodeColor(self, first_nodecolor):
        """Set the first_nodecolor for gv output.
        """
        self._first_nodecolor=first_nodecolor

    def getFirstNodeFontColor(self):
        """Return the current gv first_node_font_color.
        """
        return self._first_node_font_color

    def setFirstNodeFontColor(self, first_node_font_color):
        """Set the first_node_font_color for gv output.
        """
        self._first_node_font_color=first_node_font_color

    def getFirstNodeFontColor(self):
        """Return the current gv first_node_font_color.
        """
        return self._first_node_font_color

    def setFirstNodeFontColor(self, first_node_font_color):
        """Set the first_node_font_color for gv output.
        """
        self._first_node_font_color=first_node_font_color

    def getFirstNodeFontSize(self):
        """Return the current gv first_node_font_size.
        """
        return self._first_node_font_size

    def setFirstNodeFontSize(self, first_node_font_size):
        """Set the first_node_font_size for gv output.
        """
        self._first_node_font_size=first_node_font_size

    def getSecondNodeShape(self):
        """Return the current gv second_nodeshape.
        """
        return self._second_nodeshape

    def setSecondNodeShape(self, second_nodeshape):
        """Set the second_nodeshape for gv output.
        """
        self._second_nodeshape=second_nodeshape

    def getSecondNodeColor(self):
        """Return the current gv second_nodecolor.
        """
        return self._second_nodecolor

    def setSecondNodeColor(self, second_nodecolor):
        """Set the second_nodecolor for gv output.
        """
        self._second_nodecolor=second_nodecolor

    def getSecondNodeFontColor(self):
        """Return the current gv second_node_font_color.
        """
        return self._second_node_font_color

    def setSecondNodeFontColor(self, second_node_font_color):
        """Set the second_node_font_color for gv output.
        """
        self._second_node_font_color=second_node_font_color

    def getSecondNodeFontColor(self):
        """Return the current gv second_node_font_color.
        """
        return self._second_node_font_color

    def setSecondNodeFontColor(self, second_node_font_color):
        """Set the second_node_font_color for gv output.
        """
        self._second_node_font_color=second_node_font_color

    def getSecondNodeFontSize(self):
        """Return the current gv second_node_font_size.
        """
        return self._second_node_font_size

    def setSecondNodeFontSize(self, second_node_font_size):
        """Set the second_node_font_size for gv output.
        """
        self._second_node_font_size=second_node_font_size

    def getEdgeShape(self):
        """Return the current gv edgeshape.
        """
        return self._edgeshape

    def setEdgeShape(self, edgeshape):
        """Set the edgeshape for gv output.
        """
        self._edgeshape=edgeshape

    def getEdgeColor(self):
        """Return the current gv edgecolor.
        """
        return self._edgecolor

    def setEdgeColor(self, edgecolor):
        """Set the edgecolor for gv output.
        """
        self._edgecolor=edgecolor

    def getEdgeFontColor(self):
        """Return the current gv edge_font_color.
        """
        return self._edge_font_color

    def setEdgeFontColor(self, edge_font_color):
        """Set the edge_font_color for gv output.
        """
        self._edge_font_color=edge_font_color

    def getEdgeFontColor(self):
        """Return the current gv edge_font_color.
        """
        return self._edge_font_color

    def setEdgeFontColor(self, edge_font_color):
        """Set the edge_font_color for gv output.
        """
        self._edge_font_color=edge_font_color

    def getEdgeFontSize(self):
        """Return the current gv edge_font_size.
        """
        return self._edge_font_size

    def setEdgeFontSize(self, edge_font_size):
        """Set the edge_font_size for gv output.
        """
        self._edge_font_size=edge_font_size

    def getGVFontList(self):
        """Return the current gv font list.
        """
        return self._fonts

    def getFontPath(self):
        """Return the saved systems font path.
        """
        return self._fontpath

    def setFontPath(self, path=''):
        """set the systems font path manually.
        """
        if path == '':
         for el in findFonts():
          if "\\" in el:
           self._fonts.append(el.split("\\")[len(el.split("\\"))-1][:-4])
          elif "/" in el:
           self._fonts.append(el.split("/")[len(el.split("/"))-1][:-4])
        else:
         self._fonts=[]
         for el in findFonts(path):
          if "\\" in el:
           self._fonts.append(el.split("\\")[len(el.split("\\"))-1][:-4])
          elif "/" in el:
           self._fonts.append(el.split("/")[len(el.split("/"))-1][:-4])
        try:
         self._fonts.sort()
        except:
         pass
        self._fontpath=path
        
    def getGVFont(self):
        """Return the current gv font.
        """
        return self._gvfont

    def setGVFont(self, font):
        """Set the font for gv output.
        """
        self._gvfont=font

    def getRelFont(self):
        """Return the current relation font.
        """
        return self._relfont

    def setRelFont(self, font):
        """Set the font for relation output.
        """
        self._relfont=font

    def getBack(self):
        """Return if Back References should be used in the KeywordMap generation.
        """
        return self._back

    def setBack(self, back):
        """Set the back option.
        """
        self._back=back

    def getForth(self):
        """Return if Forward References should be used in the KeywordMap generation.
        """
        return self._forth

    def setForth(self, forth):
        """Set the forth option"""
        self._forth=forth

    def getEncoding(self):
        """Get the encoding of strings used in the classification tool.
        """
        return self._encoding

    def setEncoding(self, encoding):
        """Set the encoding of strings used in the classification tool.
        """
        self._encoding = encoding

    def getClassifyRelationship(self):
        """Get the name of the Archetype References relationship used for referencing keywords from classified content objects.
        """
        return self._classifyRelationship

    def setClassifyRelationship(self, relationship):
        """Set the name of the Archetype References relationship used for referencing keywords from classified content objects and update all existing classification references.
        """
        oldRelationship = self.getClassifyRelationship()
        self.changeClassifyRelationship(oldRelationship, relationship)
        self._classifyRelationship = relationship

    def changeClassifyRelationship(self, oldRelationship, newRelationship):
        """Change all existing classification references from 'oldRelationship' to 'newRelationship'.
        """
        if newRelationship == oldRelationship:
            return

        for keywordName in self.keywords():
            keyword = self.getKeyword(keywordName)
            for classifiedContent in keyword.getBRefs(oldRelationship):
                classifiedContent.deleteReference(keyword, oldRelationship)
                classifiedContent.   addReference(keyword, newRelationship)

    def reftypes(self):
        """Return a list of all referenceable portal types.
        """
        at = getToolByName(self, 'archetype_tool')
        typeslist=[]
        for el in at.listRegisteredTypes():
            typeslist.append(el['meta_type'])

        return typeslist

    def getClassifyTypes(self):
        """Return a list of all the types which are set as classifyable.
        """
        return self._classifytypes

    def setClassifyTypes(self, types):
        """Set the list of the classifyable types.
        """
        self._classifytypes=types

    def addClassifyType(self, type):
        """Add a type to the list of classifyable types.
        """
        if not type in self._classifytypes:
            self._classifytypes.append(type)

    def removeClassifyType(self, type):
        """Remove a type from the list of classifyable types.
        """
        try:
            self._classifytypes.remove(type)
        except ValueError:
            pass

    def returnReadMe(self):
        """Return README file for display in configlet.
        """
        from config import GLOBALS
        cdir = os.path.dirname(GLOBALS['__file__'])
        filename = os.path.join(cdir, "README.txt")
        try:
            f=open(filename,'r').read()
            return f
        except:
            return 'README.txt not found'

    def addKeyword(self, name, title="", description="", shortDescription="", uid=""):
        """Create a keyword in the current ontology. If 'uid' is specified, the referenced keyword is registered as 'name'.

        Exceptions:
            ValidationException : 'name' is not a valid XML NCName.
            NameError           : Keyword 'name' already exists in current ontology.
            AttributeError      : 'uid' references no keyword in current ontology.
        """
        if not owl.isXMLNCName(name):
            raise ValidationException("Invalid name for keyword specified")

        if self.isUsedName(name):
            raise NameError, "Keyword '%s' already exists in current ontology" % name

        storage = self.getStorage()
        if not uid:
            uid = generateUniqueId('Keyword')
            storage.invokeFactory('Keyword', uid)
        kw = getattr(storage, uid)
        if not title:
            title = name
        kw.setName(name)
        kw.setTitle(title)
        kw.setKwDescription(description)
        kw.setShortAdditionalDescription(shortDescription)
        kw.unmarkCreationFlag()
        kw.reindexObject()
        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "Added keyword %s." % name)

        return kw

    def getKeyword(self, name):
        """Return keyword 'name' from current ontology.

        Exceptions:
            NotFound            : There is no keyword 'name' in current ontology.
            ValidationException : 'name' is empty.
        """
        catalog = getToolByName(self, 'portal_catalog')

        if not name:
            raise ValidationException, "Empty keyword name."

        try:
            return catalog.searchResults(portal_type='Keyword', name=name.decode(self.getEncoding()))[0].getObject()
        except IndexError:
            raise NotFound, "Keyword '%s' not found in current ontology" % name

    def isUsedName(self, name, type="Keyword"):
        """Check if 'name' is used for 'type' already.

        Exceptions:
            ValidationException : 'name' is empty or 'type' is unknown.
        """
        try:
            if   type == "Keyword":
                return self.getKeyword(name)
            elif type == "Ruleset":
                return self.getRelation(name)
            else:
                raise ValidationException, "Unknown type for name '%s': %s" % (name,type)
        except NotFound:
            return False

    def getKeywordProposal(self, name):
        """Return keyword proposal 'name'.

        Exceptions:
            NotFound            : There is no keywordproposal 'name'.
            ValidationException : 'name' is empty.
        """
        catalog = getToolByName(self, 'portal_catalog')

        if not name:
            raise ValidationException, "Empty keyword proposal name."

        try:
            return catalog.searchResults(portal_type='KeywordProposal', name=name.decode(self.getEncoding()))[0].getObject()
        except IndexError:
            raise NotFound, "KeywordProposal '%s' not found" % name

    def delKeyword(self, name):
        """Remove keyword from ontology.
        """

        try:
            kw = self.getKeyword(name)
        except NotFound:
            return

        storage = self.getStorage()
        try:
            storage._delObject(kw.getId())
            zLOG.LOG(PROJECTNAME, zLOG.INFO,
                     "Removed keyword %s." % name)
        except KeyError:
            pass

    def keywords(self):
        """Return a list of all existing keyword names.
        """
        catalog = getToolByName(self, 'portal_catalog')

        return [kw_res.getObject().getName() for kw_res in catalog.searchResults(portal_type='Keyword')]

    def addRelation(self, name, weight=0.0, types=[], inverses=[], uid=""):
        """Create a keyword relation 'name' in the Plone Relations library, if non-existant.

        'weight' is set in any case if in [0,1]. For each item in the 'types' list from {'transitive', 'symmetric', 'functional', 'inversefunctional'} an appropiate rule is created in the Relations ruleset. For each relation name in the 'inverses' list an InverseImplicator rule is created in the Relations ruleset. The inverse keyword relation is created in the Plone Relations library if non-existant. Rules for inferring types for the inverse relation are created. If 'uid' is specified, the referenced relation ruleset is registered as relation 'name'.

        Exceptions:
            ValidationException : 'name' is not a valid XML NCName.
            NameError           : Relation 'name' already exists in current ontology.
            AttributeError      : 'uid' references no relation in current ontology.
        """
        if not owl.isXMLNCName(name):
            raise ValidationException("Invalid name for relation specified")

        if self.isUsedName(name, 'Ruleset'):
            raise NameError, "Relation '%s' already exists in current ontology" % name

        relations_library = getToolByName(self, 'relations_library')

        if not uid:
            uid = generateUniqueId('Ruleset')
            relations_library.invokeFactory('Ruleset', uid)

        ruleset = relations_library.getRuleset(uid)
        ruleset.setTitle(name)
        ruleset.reindexObject()
        ruleset.unmarkCreationFlag()

        self.setWeight  (name, weight)

        if type(types) != ListType:
            types = [types]
        self.setTypes   (name, types)

        if type(inverses) != ListType:
            inverses = [inverses]
        self.setInverses(name, inverses)

        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "Added relation %s." % name)

        return ruleset

    def getRelation(self, name):
        """Return ruleset for keyword relation 'name' of current ontology from the Plone Relations library.

        Exceptions:
            NotFound            : There is no relation 'name' in current ontology.
            ValidationException : 'name' is empty.
        """
        catalog = getToolByName(self, 'portal_catalog')

        if not name:
            raise ValidationException, "Empty relation name."

        try:
            return catalog.searchResults(portal_type='Ruleset', Title=name)[0].getObject()
        except IndexError:
            raise NotFound, "Relation '%s' not found in current ontology" % name

    def delRelation(self, name):
        """Remove the keyword relation 'name' from current ontology, if it exists.
        """
        relations_library = getToolByName(self, 'relations_library')
        try:
            relations_library.manage_delObjects(self.getRelation(name).getId())
            zLOG.LOG(PROJECTNAME, zLOG.INFO, "Removed relation %s." % name)
        except:
            pass

    def relations(self, relations_library, plus='0'):
        """Return a list of all existing keyword relation names in 'relations_library' and add ['noChange', 'deleteAll'] if plus != '0'
        """
        rel_list=['noChange', 'deleteAll']
        if plus != '0':
         for r in relations_library.getRulesets():
          rel_list.append(r.Title()) 
         return rel_list
        else:
         return [r.Title() for r in relations_library.getRulesets()]

    def getWeight(self, name):
        """Return the weight of keyword relation 'name'.

        Exceptions:
            NotFound : No relation 'name' in current ontology.
        """
        r = self.getRelation(name)
        try:
            return r.weight
        except AttributeError:
            return 0.0

    def setWeight(self, name, w):
        """Set weight of keyword relation 'name' to 'w', if 'w' >= 0.

        Exceptions:
            NotFound : No relation 'name' current ontology.
        """
        r = self.getRelation(name)

        if w >= 0.0:
            r.weight = w

    def setTypes(self, name, t):
        """Set the list of types of keyword relation 'name'.

        The list is set to t, if 't' is non-empty list from {'transitive', 'symmetric', 'functional', 'inversefunctional'}. Empty list deletes all types.
        Return the list of types of keyword relation 'name'.

        Exceptions:
            NotFound : No relation 'name' in current ontology.
        """

        r = self.getRelation(name)

        if 'transitive' in t:
            r.transitive = True
        elif hasattr(r, 'transitive'):
            delattr(r, 'transitive')

        if 'symmetric' in t:
            if not hasattr(r, 'symmetric'):
                r.invokeFactory('Inverse Implicator', 'symmetric')
                r.symmetric.setInverseRuleset(r.UID())
                r.symmetric.setTitle('Symmetric')
        else:
            try:
                r.manage_delObjects('symmetric')
            except AttributeError:
                pass
    
        if 'functional' in t:
            if not hasattr(r, 'functional'):
                r.invokeFactory('Cardinality Constraint', 'functional')
                r.functional.setMinTargetCardinality(0)
                r.functional.setMaxTargetCardinality(1)
        else:
            try:
                r.manage_delObjects('functional')
            except AttributeError:
                pass

        if 'inversefunctional' in t:
            if not hasattr(r, 'inversefunctional'):
                r.invokeFactory('Cardinality Constraint', 'inversefunctional')
                r.inversefunctional.setMinSourceCardinality(0)
                r.inversefunctional.setMaxSourceCardinality(1)
        else:
            try:
                r.manage_delObjects('inversefunctional')
            except AttributeError:
                pass

    def getTypes(self, name):
        """Get list of types for keyword relation 'name'.

        Exceptions:
            NotFound : No relation 'name' in current ontology.
        """
        ruleset = self.getRelation(name)

        result = []
        try:
            if ruleset.transitive:
                result.append('transitive')
        except AttributeError:
            pass

        result.extend([rule.getId() for rule in ruleset.getComponents(interfaces.IRule) if rule.getId() in ('symmetric', 'functional', 'inversefunctional')])

        return result
        
    def setInverses(self, name, i):
        """Set inverse relations of keyword relation 'name'.

        Inverse relations are set to relations in 'i', if 'i' is non-empty list of relation names. Empty list deletes all inverses. All relations in 'i' are created, if non-existant. Inferring types for relations in 'i' are created from the types of relation 'name'.

        Exceptions:
            NotFound : No relation ruleset 'name' in current ontology.
        """
        ruleset = self.getRelation(name)
        current = self.getInverses(name)
        new = [x for x in i if not x in current]
        obsolete = [x for x in current if not x in i]

        for o in obsolete:
            iruleset = self.getRelation(o)
            irules = iruleset.getComponents(interfaces.IRule)
            irules = [rule for rule in irules if rule.getId().startswith('inverseOf')]
            iruleset.manage_delObjects([rule.getId() for rule in irules if rule.getInverseRuleset().Title() == ruleset.Title()])

        ruleset.manage_delObjects([rule.getId() for rule in ruleset.getComponents(interfaces.IRule) if rule.getId().startswith('inverseOf_') and rule.getInverseRuleset().Title() in obsolete])

        for inverse in new:
            try:
                self.getRelation(inverse)
            except NotFound:
                self.addRelation(inverse)

        for inverse in i:
            inverse_ruleset = self.getRelation(inverse)

            types         = self.getTypes(name)
            inverse_types = [t for t in types if t in ['transitive', 'symmetric']]      + \
                            ['inversefunctional' for i in range('functional' in types)] + \
                            ['functional' for i in range('inversefunctional' in types)]

            self.setTypes(inverse, inverse_types)

            if not hasattr(ruleset, 'inverseOf_' + inverse_ruleset.getId()):
                ruleset.invokeFactory('Inverse Implicator', 'inverseOf_' + inverse_ruleset.getId())
                getattr(ruleset, 'inverseOf_' + inverse_ruleset.getId()).setTitle('inverseOf: ' + inverse)
                getattr(ruleset, 'inverseOf_' + inverse_ruleset.getId()).setInverseRuleset(inverse_ruleset.UID())

            if not hasattr(inverse_ruleset, 'inverseOf_' + ruleset.getId()):
                inverse_ruleset.invokeFactory('Inverse Implicator', 'inverseOf_' + ruleset.getId())
                getattr(inverse_ruleset, 'inverseOf_' + ruleset.getId()).setTitle('inverseOf: ' + name)
                getattr(inverse_ruleset, 'inverseOf_' + ruleset.getId()).setInverseRuleset(ruleset.UID())

    def getInverses(self, name):
        """Get inverse relations for the relation 'name'.

        Exceptions:
            NotFound : No relation ruleset 'name' in current ontology.
        """
        ruleset = self.getRelation(name)
        return [rule.getInverseRuleset().Title() for rule in ruleset.getComponents(interfaces.IRule) if rule.getId().startswith('inverseOf_')]
        
    def addReference(self, src, dst, relation, ):
        """Create an Archetype reference of type 'relation' from keyword with name
        'src' to keyword with name 'dst', if non-existant.

        'src' and 'dst' are created, if non-existant. The reference is created through Plone Relations library, so relation-specific rulesets are honored.

        Exceptions:
            NotFound            : No relation 'relation' in current ontology.
            ValidationException : Reference does not validate in the relation ruleset or 'src' or 'dst' are invalid XMLNCNames
        """
        zLOG.LOG(PROJECTNAME, zLOG.INFO,
                 "%s(%s,%s)." % (relation, src, dst))

        relations_library = getToolByName(self, 'relations_library')

        try:
            kw_src  = self.getKeyword(src)
        except NotFound:
            kw_src  = self.addKeyword(src)

        try:
            kw_dst  = self.getKeyword(dst)
        except NotFound:
            kw_dst  = self.addKeyword(dst)

        process(self, connect=((kw_src.UID(), kw_dst.UID(), self.getRelation(relation).getId()),))


    def delReference(self, src, dst, relation):
        """Remove the Archetype reference of type 'relation' from keyword with
        name 'src' to keyword with name 'dst', if the reference exists.

        'src' and 'dst' are created, if non-existant. The reference is removed through Plone Relations library, so relation-specific rulesets are honored.

        Exceptions:
            NotFound            : No relation 'relation' in current ontology.
            ValidationException : Unreference does not validate in the relation ruleset.
        """
        try:
            kw_src = self.getKeyword(src)
            kw_dst = self.getKeyword(dst)
        except NotFound:
            return

        process(self, disconnect=((kw_src.UID(), kw_dst.UID(), self.getRelation(relation).getId()),))

    # ZMI wrappers.
    def manage_addKeyword(self, name, title='', shortAdditionalDescription='', description='', REQUEST=None):
        """Add new keyword.
        """
        self.addKeyword(name, title, description, shortAdditionalDescription)

        if REQUEST is not None:
            return self.manage_main(REQUEST)

    def manage_addRelation(self, name, title='', factor=1, REQUEST=None):
        """Add new relation between keywords.
        """
        self.addRelation(name, factor)

        if REQUEST is not None:
            return self.manage_relations(REQUEST)

    def manage_delRelations(self, ids, REQUEST=None):
        """Delete keyword relations.
        """
        for name in ids:
            self.delRelation(name)

        if REQUEST is not None:
            return self.manage_relations(REQUEST)

    def manage_changeFactors(self, name, factor=1, REQUEST=None):
        """Change relevancy factor/weight for relation.
        """
        self.setWeight(name, factor)

        if REQUEST is not None:
            return self.manage_relations(REQUEST)

    ### End of new API.

    def setStorageId(self, name):
        """Set id of current storage.
        """
        self._storage = name

    def getStorageId(self):return self._storage

    def getStorage(self):
        """Return current keyword storage object.
        """
        urltool = getToolByName(self, 'portal_url')
        portal = urltool.getPortalObject()

        kwstorage = getattr(portal, self.getStorageId(), None)

        if kwstorage is None: #create
            pt=getToolByName(self, 'portal_types')
            pt.getTypeInfo('Ontology').global_allow=True
            portal.invokeFactory('Ontology',
                                 self.getStorageId(),
                                 title='Ontology')

            pt.getTypeInfo('Ontology').global_allow=False

            kwstorage = getattr(portal, self.getStorageId(), None)

        return kwstorage

    def isAllowed(self, obj):
        """Return true if current user is allowed to access obj.

        This is solely to swallow Unauthorized exceptions.
        """
        if obj is None: return 0

        try:
            if getSecurityManager().validate(self, self, obj.getId(), obj):
                return 1
        except Unauthorized:
            return 0

        return 0

    def search(self, kwName, links="all"):
        """Search Content for a given keyword with name 'kwName'.

        By default follow all link types.
        """

        keywords = self.getRelatedKeywords(kwName, links=links,
                                           cutoff = self.getSearchCutoff())

        results = []

        for kw in keywords.keys():
            obj = self.getKeyword(kw)
            rels = obj.getBRefs(self.getClassifyRelationship()) or []

            res = [(keywords[kw], x) for x in rels if self.isAllowed(x)]
            results.extend(res)

        results =  _unifyRawResults(results)

        results.sort()
        results.reverse() #descending scores
        return results

    def searchFor(self, obj, links="all"):
        """Search related content for content object.
        """

        # search not possible for non AT types
        if not getattr(obj, 'isReferenceable', 0): return []

        keywords = obj.getRefs(self.getClassifyRelationship()) or []

        results = []

        for kw in keywords:
            if kw is not None:
                results.extend(self.search(kw.getName(), links=links))

        results =  _unifyRawResults(results)

        # remove object
        results = [x for x in results if x[1]!=obj]
        results.sort()
        results.reverse()

        return results

    def getRelatedKeywords(self, keyword, fac=1, result={}, links="all", cutoff=0.1):
        """Return list of keywords, that are related to keyword with name 'keyword'.
        """

        try:
            kwObj = self.getKeyword(keyword)
        except NotFound: # nonexistant keyword
            return {}

        # work with private copy w/t reference linking
        result = result.copy()

        # if necessary initialize keyword in result list
        if not result.has_key(kwObj.getName()):
            result[kwObj.getName()] = fac

        # proper link types initialization
        if type(links) == StringType:
            if links == "all":
                rl = getToolByName(self, 'relations_library')
                links = self.relations(rl)
            else:
                links = [links]

        children = self._getDirectLinkTargets(kwObj, fac, links, cutoff)
        result = self._getRecursiveContent(kwObj, children, result, links, cutoff)

        return result

    def _getDirectLinkTargets(self, kwObj, fac, links, cutoff):
        children=[]

        for rel in links:
            relfac = self.getWeight(rel) * fac
            children.extend([(relfac, x)
                             for x in (kwObj.getReferences(rel) or []) if x is not None and relfac>cutoff])

        return _unifyRawResults(children)

    def _getRecursiveContent(self, kwObj, children, result, links, cutoff):
        for c in children:
            cname = c[1].getName()
            if not result.has_key(cname):
                result[cname] = c[0]

                recursive = self.getRelatedKeywords(cname, c[0],
                                                    result, links, cutoff)

                if recursive.has_key(kwObj.getName()): #suppress direct backlinks
                    del recursive[kwObj.getName()]

                for kw in recursive.keys():
                    if not result.has_key(kw):
                        result[kw] = recursive[kw]

        return result

    def setSearchCutoff(self, cutoff):
        if type(cutoff) != FloatType: cutoff = float(cutoff)
        if cutoff < 0: cutoff = 0

        self._cutoff = cutoff

    def getSearchCutoff(self):
        return self._cutoff

    def searchMatchingKeywordsFor(self, obj, search, exclude=[], search_kw_proposals='false', search_linked_keywords='true'):
        """Return keywords matching a search string.
        """
        #XXX obj in method signature is obsolete
        storage = self.getStorage()
        catalog = getToolByName(self, 'portal_catalog')

        kws = dict(storage.objectItems('Keyword'))

        for item in storage.objectValues('Keyword'):
            if item.title:
                kws.update({item.title: item})

        result = difflib.get_close_matches(search.decode(self.getEncoding()), kws.keys(), n=5, cutoff=0.5)
        result = [kws[x] for x in result]

        extresult=[]
        if search_linked_keywords == 'true':
         [extresult.extend(x.getLinkedKeywords()) for x in result]


        if search_kw_proposals=='true':
         kwps = catalog.searchResults(portal_type='KeywordProposal')
         kwpsdict={}
         for el in kwps:
          if el.getObject().getParentNode().getId() != 'accepted_kws':
           kwpsdict.update({el.getObject().getId():el.getObject()})
         result2 = difflib.get_close_matches(search, kwpsdict.keys(), n=5, cutoff=0.5)
         result2 = [kwpsdict[x] for x in result2]
         for el in result:
          for el2 in result2:
           if el2.getId()==el.getId() or el2.title_or_id() == el.title_or_id():
            result2.remove(el2)
         result.extend(result2)
         result.extend(extresult)

        #remove duplicates & excludes

        if type(exclude) != ListType:
            exclude = [exclude]

        set = []
        [set.append(i) for i in result if (not i in set) and (i not in exclude)]

        if len(set) > 20:
            set = set[0:20]
        return set

    def useGraphViz(self): return self._use_gv_tool

    def generateGraphvizMap(self):
        """Generate graph source code for GraphViz.
        """
        storage = self.getStorage()
        catalog = getToolByName(self, 'portal_catalog')

        kws=[kw_res.getObject() for kw_res in catalog.searchResults(portal_type='Keyword')]

        dot = KeywordGraph(self.getGVFont(), self.getRelFont(), self.getFocusNodeShape(), self.getFocusNodeColor(), self.getFocusNodeFontColor(), self.getFocusNodeFontSize(), self.getFirstNodeShape(), self.getFirstNodeColor(), self.getFirstNodeFontColor(), self.getFirstNodeFontSize(), self.getSecondNodeShape(), self.getSecondNodeColor(), self.getSecondNodeFontColor(), self.getSecondNodeFontSize(), self.getEdgeShape(), self.getEdgeColor(), self.getEdgeFontColor(), self.getEdgeFontSize())
        
        dot.graphHeader(kws[0])

        for node in kws:
            dot.firstLevelNode(node)
            rels = node.getRelations() 
            for rel in rels:
                  obs = node.getReferences(rel)
                  try:
                    obs.remove(self)
                  except ValueError: # self not in list
                    pass
                  for cnode in obs:
                    dot.relation(node, cnode, rel)

        dot.graphFooter()

        return dot.getValue()

InitializeClass(ClassificationTool)
