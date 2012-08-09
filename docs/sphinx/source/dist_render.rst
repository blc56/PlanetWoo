Distributed Rendering - Overview
=================================

Configfile
-----------

Distributed rendering is controlled through a json configuation file. The file should contain a dictionary with the following attributes.

.. _global_options_mapserver:

Global Options
---------------

mapfile_path
 A list of (local) paths to the mapfiles to be rendered. 

shapefile_path
 A list of (local) shapefile paths that are required for rendering. Specify the .shp suffix, and all files with a matching basename will be copied.

data_file_dest
 Path to a directory where working files are copied to render nodes.

render_nodes
 A list of dictionaries, one per render node, with the following attributes:
  :address:
   The ssh address of the render node.
  :num_threads:
   The number of threads available for rendering on the render node.

map_extent
 The maximum extent of the map in a list of ``min_x, min_y, max_x, max_y``. This will be drawn in a single tile at zoom level ``start_zoom``. NOTE: This MUST be square. Example: ``[-10, -10, 10, 10]``

start_zoom
 Zoom level at which tiles will start to be rendered (inclusive).

stop_zoom
 Zoom level at which tiles will stop being rendered (inclusive).

start_tile_x
 X coordinate of the tile which will be the root of rendered tiles. 

start_tile_y
 Y coordinate of the tile which will be the root of rendered tiles. 

min_num_jobs
 Optional. Specifies a minimum number of jobs that should be created and sent to render nodes. This is useful more evenly distributing the workload between render nodes/threads. 

render_script
 TODO: better explanation
 The command that is run inside a shell on render nodes to render tiles. Example:``source ~/env.sh && ~/planetwoo/scripts/render_to_csv.py``. 

start_checks_zoom
 Optional. Default: ``0``. Zoom level at which the renderer will start checking for tiles which contain no geometries or are completely contained by a geometry.

check_full
 Optional. Default: ``true``. ``true`` or ``false``. Toggles if the renderer will check for tiles that are completely contained by a geometry. It is a good idea to turn this off for linear feature layers for performance reasons.

output_prefix
 Prepended to output files on render nodes. 

Cutter Options
-----------------

:ref:`Cutter Options <cutter_config>`

Storage Manager Options
-----------------

:ref:`Storage Manager Options <storage_manager_config>`

Renderer Options
-----------------

:ref:`Renderer Options <renderer_config>`

Starting a Distributed Render
------------------------------

::

 fab -f fabric/dist_render.py -H localhost dist_render:<path_to_config.json>

Monitoring Progress
---------------------

::

 fab -f fabric/dist_render.py -H localhost watch_progress:<path_to_config.json>


Retrieving the Results
-----------------------

This script will download the resultant .csv files into the current directory.

::

 fab -f fabric/dist_render.py -H localhost get_results:<path_to_config.json>

Loading Results into Postgres
------------------------------

This command will load resultant .csv files into postgres. Each layer has a two tables: one containing the quadtree structure, and one containing the rendered tiles. WARNING: The tables specified will be dropped and recreated.

::

 fab -f fabric/dist_render.py -H localhost load_results:<path_to_config.json>,<connect_str>,<node_table>,<image_table>,<results_directory>


Serving the Results
--------------------

::

 www/slippy_server.py -p 8080 -l "<node_table>,<image_table>"

