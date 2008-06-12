from keywordgraph import KeywordGraph
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.atapi import *
from types import StringType

mapSchema = BaseSchema + Schema((
    ImageField("MapGraphic"),
    TextField("MapData",
              default_content_type="text/html",
              default_output_type="text/html",
              ),

    ))

class Map(BaseContent):

    meta_type = portal_type = archetype = "Ontology Map Graph"
    content_icon = "keyword.gif"
    schema = mapSchema
    actions = (
        {'name' : "View",
         'id' : "view",
         'action' : "string: ${object_url}/map_view",
         'category' : "object_tabs",
         },

        )

    def at_post_create_script(self):
        self.updateGraphvizMap()

    def updateGraphvizMap(self):
        """Update Map cached images. Returns string containing error messages, empty if none.
        """
        ctool = getToolByName(self, 'portal_classification')
        gvtool = getToolByName(self, 'graphviz_tool')

        if not gvtool.isLayouterPresent():
            raise NotFound(gvtool.getLayouter())

        g = ctool.generateGraphvizMap()

        (result, error) = gvtool.renderGraph(g, options=["-Tpng",])
        self.setMapGraphic(result, mimetype="image/png")

        (result, error) = gvtool.renderGraph(g, options=["-Tcmap",])
        self.setMapData(result, mimetype="text/html")

        return error

registerType(Map)
