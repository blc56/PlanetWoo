.. _storage_manager_config:

Storage Manager Options
===============

In a config file, the storage manager is chosen with the following options.

storage_type
 Optional. Default: ``"csv"``. One of ``"csv"`` or ``"multi"``.

CSV Storage 
------------
A CSV Storage Manager stores rendered tiles into two .csv files. One file ending in "_tree.csv" contains a quad tree structure for the tiles. Another file ending in "_images.csv" contains pairs of image id's and image file blobs. These files are designed to be easily loaded into other storage managers to serve the tiles.

output_prefix
 A path that is prepended to the output csv files. 

