Future Enhancements
=====================

Configurability
-----------------
Add in hooks for point label placement: left, right, etc.
Work out a solution for "Auto" label placement.

Label Wrap Characters
----------------------
Instead of wrapping on whitespace characters, add the ability
to wrap on a list of characters or regex matches.

Cutters
-------------
Add a cutter that uses a spacial (rtree?) index. Maybe libspatialindex?
Add a CutterCache that can be used by MultiRenderer/Cutter to cache cut() results for layers which have identical features.

Config file Cleanups
---------------------
Make the config file less mapserver specific. Consider merging the config files formates used by dynamic_slippy_sever.py and dist_render.py

Add the option for automatic configuration of DATA paths in mapfiles based on "data_file_dest".

Mapnik Renderer
-----------------
Maybe?

