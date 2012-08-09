Purpose
===================

PlanetWoo was conceived after searching for an efficient method to render map tiles. To achieve fast render times and storage efficiency, PlanetWoo avoids rendering and storing redundant map tiles.

Quad Tree
----------
See here for an overview of OSM style "slippy" maps.
http://wiki.openstreetmap.org/wiki/Slippy_Map

A slippy map can be viewed as a quad tree. Zoom level 0 contains a single tile which contains the entire map. It is the root node. Zoom level 1 contains 4 tiles each comprising a fourth of the map. At each increased zoom level tiles are recursively split into 4 sub tiles. Each tile is represented as a "node". The recursive structure of the "nodes" is a Quad Tree.

http://en.wikipedia.org/wiki/Quad_tree

Blank Tiles
------------
Observe that if the bounding box of a node contains no features, then all of its sub nodes will a will also contain no features. This is referred to in PlanetWoo as a "blank" node.

Full Tiles
------------
Observe that if the bounding box of a node is complete contained by a feature, then all of tis sub nodes will also be complete contained by that feature. This is referred to in PlanetWoo as a "full" node.


