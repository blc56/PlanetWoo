Future Enhancements
=====================

Update Docs
------------
Try to keep up with the churn.

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

Better Thread Efficiency
------------------------
I really hate writing multithreaded applications in python. Right now a "job" gets split into nodes and we keep sending those jobs to threads. Once a thread finishes, we send it a new "job". The problem is that the "jobs" end up being unbalanced and one always seem to take way longer then all the rest of them. We need a more granular method of doing this.

Mapnik Renderer
-----------------
Maybe?

