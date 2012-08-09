
.. _label_render:

Distributed Label Rendering
======================================================

Overview
---------

PlanetWoo has a special renderer for labels. Mapscript and a mapfile are used to query for the features which should be labeled in a given tile. The features are then labeled using a deterministic positioning algorithm that ensures consistency for labels across each tile.

Configfile
-----------

renderer_type
 Set to ``"label"`` to use a ``LabelRenderer``.

mapfile_path
 A path to the mapfile used to query for features.

mapserver_layers
 A list of layer names from ``mapfile_path`` that contain features that should be labeled.

label_col_index
 Index of the feature attribute which contains the label.

min_zoom
 Optional. Default: ``0``. Zoom levels strictly less than this number will always be rendered as blank tiles.

max_zoom
 Optional. Default: ``0``. Zoom levels strictly greater than this number will always be rendered as blank tiles and flagged as leaf nodes.

point_labels
 Boolean. Default: ``false``. ``true`` for point label placement algorithm. ``false`` for polygon label placement algorithm. See :ref:`here<label_placement_algs>`

label_classes
 A dictionary of lists.

 :key:
  Layer name. Corresponds with ``mapserver_layers``.
 :value:
  A list of dictionaries. Each dictionary represents a ``LabelClass`` which controls label styling.

Label Class Configuration
--------------------------
Each label class is configured as a dictionary with the following attributes.

font
 Path to a .ttf font file.

font_size
 An integer.

font_color_fg
 Controls the color of the label text. A list of ``[r, g, b, a]`` values from 0 to 1.

font_color_bg
 Optional. Default: disabled. Controls the color of the label text halo. A list of ``[r, g, b, a]`` values from 0 to 1.

mapsever_query
 Optional. Default: ``"(1 === 1)"``. A mapserver query string used to determine which features correspond to this ``LabelClass``.

min_zoom
 An integer. This ``LabelClass`` will not be drawn on zoom levels strictly less than this number.

max_zoom
 An integer. This ``LabelClass`` will not be drawn on zoom levels strictly greater than this number.

``label_classes`` Example
----------------------------

::
 
 "label_classes": {
     "us_plc_polygon": [{
         "font": "arial",
         "font_size": 18,
         "font_color_fg": [0, 0, 0, 1],
         "font_color_bg": [1, 1, 1, 1],
         "mapserver_query": "([pop] > 250000)",
         "min_zoom": 8,
         "max_zoom": 19
     },
     {
         "font": "arial",
         "font_size": 16,
         "font_color_fg": [0, 0, 0, 1],
         "font_color_bg": [1, 1, 1, 1],
         "mapserver_query": "([pop] > 10000 and [pop] <= 250000)",
         "min_zoom": 8,
         "max_zoom": 19
     },
     {
         "font": "arial",
         "font_size": 14,
         "font_color_fg": [0, 0, 0, 1],
         "mapserver_query": "([pop] <= 10000)",
         "min_zoom": 8,
         "max_zoom": 19
     }
 ]
 }

.. _label_placement_algs:


Point Label Placement
-----------------------

Point labels are placed next to a feature's centroid.

Polygon Label Placement
-----------------------

Polygon labels are placed within the polygon. If they do not fit, or cannot be drawn without colliding with another label they are not drawn. A ``LabelRenderer`` attempts to position a label every ``label_spacing`` pixels inside of a polygon. 

Label Wrapping
---------------
If a label is determined too long to be rendered without artifacts a ``LabelRenderer`` will attempt to word wrap the label by splitting it across space characters.

Avoiding Label Collisions Between Layers
-----------------------------------------

If multiple ``LabelRenderer`` layers are drawn using :ref:`multi layer rendering<dist_multi>`. A ``LabelRenderer`` will ensure that its labels do not collide with labels drawn on preceding layers.


.. vim:set et
.. vim:set ts=1
.. vim:set sw=1

