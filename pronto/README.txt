PloneOntology Readme

  Contents

    1. Overview

    2. Requirements

    3. Installation

    4. Usage


  Overview

    Features:

      * classify content with keywords from an (expandable) ontology

      * related content is displayed in a portlet, even if not
      classified with the same keyword (but with a related one...)

      * import and export of keyword-ontologies via W3C's Web 
      Ontology Language (OWL)

      * Graphviz support visualizes the keywords and their relations 
      within an ontology

      * adding keywords and relations to an ontology through a special 
      workflow

      * javascript sarissa support for easier classification or
      keyword adding


  Requirements

    required Software:

      * Zope 2.7, 2.8 or higher with Plone 2.1 or higher -- 
      "http://plone.org/products/plone/":http://plone.org/products/plone/

        *Note that PloneOntology may work with Plone 2.0.5, but that
        this is not officially supported.*

      * Relations 0.7 (UNRELEASED) from "http://svn.plone.org":http://svn.plone.org
      is needed when running Plone 2.5.x -- 
      "http://svn.plone.org/svn/archetypes/Relations/trunk/":http://svn.plone.org/svn/archetypes/Relations/trunk/
      
       * for Plone 2.1.x the latest release Relations 0.6b will do -- 
       "http://plone.org/products/relations":http://plone.org/products/relations
      
      * Archetypes 1.3.2. or higher (comes with Plone nowadays) -- 
      "http://sourceforge.net/projects/archetype":http://sourceforge.net/projects/archetype

      * The latest environment we use consists of Zope 2.9.7, Plone 2.5.3 and Relations 0.7 (UNRELEASED)

    optional Software:

      * Graphviz (Graph Visualization Software) -- 
      "http://www.graphviz.org/":http://www.graphviz.org/

      * SchemaWeb - resource for ontologies in the owl format. Try importing
      some of these to see how PloneOntology works. (Here we stumbled upon the
      beerontology that we use as an example. Thank you, David Aumueller!) -- 
      "http://www.schemaweb.info/":http://www.schemaweb.info/

    For the most convenient usage, browser clients should have 
    javascript enabled. Also javascript is required when adding
    References within KeywordProposals. This seems to be a limitation
    of the addable functionality in the Archetypes ReferenceWidget.

  Installation

    In the Plone Setup *Add/Remove Products* portlet install the 
    required software (Relations) before installing PloneOntology. If the 
    install was successfull one should see an *Add-on Product 
    Configuration* portlet for PloneOntology.

  Usage

    PloneOntology Setup:

      Tab *properties*:
      
       * general
       
         *Search Cutoff*: defines how *far* will be searched for 
         related content. Basicly a cutoff of 1 means that only 
         related content is shown which has been classified with 
         the exact same keyword (although this will depend on how 
         one sets up the relations...see also next section). The 
         cutoff should lie between 0 (exclusive) and 1. A Low cutoff
         will yield more related content items. High cutoff will yield
         less related content items (but this content will be highly
         related)

         *Keyword Storage*: the id of the folder which holds the 
         keywords. This folder is a special folder which comes with 
         PloneOntology and will be automatically created upon first
         access. Note that this behaviour will change in the future
         as a nasty quickinstaller bug that forced this, vanished
         in newer versions.
         
         *Types that Allow Classification*: choose the content types
         that shall support classification, i.e 'ATDocument' if you
         want all standard Documents to be classifiable.

       * graphviz general
       
         *Forward Relation*: controlls how the Graph is drawn. Will
         show all Relations that _go away_ from the central Keyword.
         Yet again, changing this value may take a while (see Graphviz
         Layouter for that).

         *Backward Relations*: controlls how the Graph is drawn. Will
         show all Relations that _point to_ the central Keyword.
         (If you want both directions, just activate both.) Here again,
         changing this value may take a while (see Graphviz Layouter for
         that).

         *Graphviz Layouter*: choose the layout algorithm for the
         automatic graph generation of the keyword map. 
         quote from graphviz.org:
         -dot makes ``hierarchical'' or layered drawings of directed graphs.
         The layout algorithm aims edges in the same direction (top to bottom,
         or left to right) and then attempts to avoid edge crossings and reduce
         edge length.
         -neato and fdp make ``spring model'' layouts. neato uses the
         Kamada-Kawai algorithm, which is equivalent to statistical
         multi-dimensional scaling. fdp implements the Fruchterman-Reingold
         heuristic including a multigrid solver that handles larger graphs
         and clustered undirected graphs.
         -twopi radial layout, after Graham Wills 97. The nodes are placed on
         concentric circles depending their distance from a given root node.
         -circo circular layout, after Six and Tollis 99, Kauffman and Wiese 02.
         This is suitable for certain diagrams of multiple cyclic structures such
         as certain telecommunications networks.
         You can test different layouts to find which represents your keywordbase
         best. Note though that this may take a while on sites with 
         many Keywords, as all the Keyword Graphs are redrawn. Probably
         it is best to try this on a test site first...
         
         *Keyword Font*: set the font in which the keywords are displayed
         in the graph generated by graphviz.
         
         *Arrow Font*: set the font in which name of the relations between
         the keywords are displayed in the graph generated by graphviz.

       * focus keyword appearance, first keyword appearance, second keyword appearance, arrow appearance
       
         The following settings concern the graphviz output for the
         displayed keywords and relations between them (arrows). When
         browsing the ontology, the focus keyword is the one you are just
         viewing. The first keywords are the ones directly related to the
         focus keyword. The second keywords are the keywords directly
         related to the first keyword (but not directly to the focus keyword).
         
         *Shape*: select the shape of the arrow or the shape
         that surrounds the keywordname in the graph.
         
         *Fillcolor*: set the color that fills the *shape*. Use either
         words or the html color coding starting with "#" (i.e. "blue" 
         or "#0000ff")
         
         *Fontcolor*: set the fontcolor. The usage is the same as for
         fillcolor.
         
         *Fontsize*: set the fontsize in pixel.

      Tab *relations*:

        All relation rulsets from the Relations Library should be 
        displayed here. One can edit the relevance factor of the 
        relations here - preferably it should be between 0 (unrelated) 
        and 1 (identical). Lets assume a ruleset *synonymOf' which
        states that a keyword A is synonym to a keyword B and the 
        other way around. Content classified with keyword A is thus 
        VERY closely related to content classified with keyword B, so 
        the relevance factor should be 1.
        
      Tab *import/export*:

        An existing Ontology in the OWL format
        ("http://www.w3.org/TR/owl-ref/":http://www.w3.org/TR/owl-ref/)
        can be imported into the site. Complex classes/set operations,
        local property restrictions and external references are
        currently unsupported, though. The import might take a while,
        because graphs are created for each keyword. An example OWL file
        can be found in the *doc* folder of this product.

        Also the ontology of a site can be exported to an OWL file.

      Tab *readme*:

        shows this text...

    Adding Relation Rulesets:

      Relation Rulesets define the possible relations between 
      Keywords e.g. synonym, parent, etc. Rulesets can either be 
      added through the web or via import of an OWL file. For 
      OWL import see above. The example OWL file in the *doc* folder 
      includes examples for custom rulesets.

      Adding a ruleset through the web is done in the *Relations
      Library* folder. Within a ruleset one or more rules can be
      added. E.g. a ruleset *child of* may have an *Inverse
      Implicator* rule to the ruleset *parent of*, while a ruleset 
      *synonym* may have an *Inverse Implicator* rule to
      itself. This ensures all needed relations for logical 
      consistency are created when necessary. For more information 
      see the *README.txt* and other documentation of the
      *Relations* Product. 

    Importing Keywords from a file:

      See help on the import/export tab.

    Adding Keywords and Relations between Keywords through the web:

      For a member of the portal the frist step in adding a keyword 
      to the ontology is to add a KeywordProposal. Relations to 
      existing keywords should be added within the edit form of this 
      KeywordProposal. In order to become real Keywords,
      KeywordProposals have to go through a special workflow. First 
      it gets submitted and gets into the *pending* state. Now a
      reviewer can *approve* the KeywordProposal. This approval step 
      differs from the default workflow. First of all after approval 
      the KeywordProposal becomes a permanent Keyword which can not 
      be edited by members. The Keyword gets created along with its 
      Relations to the other keywords. Secondly the KeywordProposal 
      moves to a special folder *Accepted KW Proposals*. This was done 
      in order to have an overview of the keywords and relations that 
      have been added by the members of a portal. These
      KeywordProposals can be deleted without affecting the 
      corresponding Keywords. If one wants to add a Relation between 
      two existing Keywords through the web, one should use the 
      RelationProposal. RelationProposals are added (and treated by 
      the workflow) similar to the KeywordProposals. Accepted 
      RelationProposals are also saved in the *Accepted KW Proposals* folder.

    Classifying content and the related portlet:

      For all content types that are enabled for classification an
      additional object tab is displayed, which allows to edit the
      keyword references of that object.
      To add a new keyword, first search for candidates. From the
      result list pick the ones you want to include and press the
      'Add' button.
      Removal of keywords is similar. Just select the ones to delete
      and press the 'Delete' button.
      As soon as you classified some objects within your portal, the
      related portlet shows related content, ranked according to Plone
      Ontologies scoring mechanism.

    Making a content type classifiable:

      To make a custom Archetypes content type classifiable select it
      in the list of content types within the Plone Ontology configuration
      panel. In order to make your own custom content types referencable,
      they should be based on Archetypes (and thus be referencable).Of course
      you will have to select them also in the Plone Ontology configuration
      panel.

    Getting Graphviz to work with PloneOntology

      After the Graphviz installation make sure that the graphviz 
      layouters are found in the system path. If they are not, change 
      the *GV_BIN_PATH* variable in config.py in the *PloneOntology* 
      products folder (be sure to escape the escape character if
      using windows). Also changing the Graphviz Font to some font
      installed on your system in the Plone Ontology configuration
      panel might help to solve some problems.
