DROP TABLE IF EXISTS north_america_tree;

CREATE TABLE north_america_tree 
(
node_id INTEGER PRIMARY KEY,
zoom_level INTEGER,
tile_x INTEGER,
tile_y INTEGER,
image_id INTEGER,
is_leaf BOOLEAN,
is_blank BOOLEAN,
is_full BOOLEAN
);

COPY north_america_tree FROM '/home/excensus/planetwoo/planetwoo/tests/unit/tree.csv' WITH CSV HEADER;

CREATE INDEX north_america_tree_zoom on north_america_tree (zoom_level);
CREATE INDEX north_america_tree_tile_x on north_america_tree (tile_x);
CREATE INDEX north_america_tree_tile_y on north_america_tree (tile_y);

