.. _renderer_config:

Renderer Configuration
======================

In a config file, the renderer is chosen with the following options.

renderer_type
 Optional. Default: ``"mapserver"``. One of ``"mapserver"``, ``"label"``, or ``"multi"``.

Mapserver
---------

DATA paths in mapserver should take into account that files listed in ``shapefile_path`` are copied to ``data_file_dest`` on render nodes. TODO: make this configuration more convenient. It is possible to use any CONNECTIONTYPE, but shapefiles seem to be the fastest.

min_zoom
 Optional. Default: ``0``. Zoom levels strictly less than this number will always be rendered as blank tiles.

max_zoom
 Optional. Default: ``0``. Zoom levels strictly greater than this number will always be rendered as blank tiles and flagged as leaf nodes.

mapserver_layers
 Layers that should be rendered from the mapfile.

cache_fulls
 Optional. Default: ``true``. If ``true``, assume that every "full" (see: ``check_full``) node will have the same tile image. Cache that image and avoid drawing it every time a "full" node is rendered. Turn this off for thematic polygon maps.

img_buffer
 Optional: Default: ``0``. Number of extra pixels to render around each tiles. The extra pixels are then cropped out of the final tile. Useful for avoiding edge artifacts caused by Mapserver.

tile_buffer
 Optional: Default: ``0``. In pixels. Converted to mapping coordinates and buffered around each tile's bounding box when selecting the features to be drawn. Useful when a feature's geometry may not enter a tile's bounding box, but it's rendered representation would; e.g. a linear feature which is draw with a pixel width > 0. Similar to Mapservers ``"tile_map_edge_buffer"`` METADATA option.

Mapserver Speed Tips
--------------------

Keep the mapfile as simple as possible.

If the shapefile you are rendering contains lots of smaller geometries, try creating a ``shptree`` index. Using ``stop_zoom`` for ``depth`` seems to work well.

::

 shptree <shapefile.shp> <depth>


Multi
------
:ref:`Rendering Multiple Layers <dist_multi>`

Label
------
:ref:`Label Rendering <label_render>`

