#!/usr/bin/env python
import sys
sys.path.append('../../')
import tiletree
import tiletree.fsstorage
import tiletree.csvstorage
import tiletree.mapserver
import tiletree.shapefile
import tiletree.postgres
import tiletree.pil
import tiletree.splitstorage

def null_test():
	storage_manager = tiletree.NullStorageManager()
	renderer = tiletree.NullRenderer()
	#cutter = tiletree.NullGeomCutter()
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	generator = tiletree.QuadTreeGenerator()
	min_x, min_y, max_x, max_y = cutter.bbox()
	generator.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=8)

def null_fs_tree_test():
	storage_manager = tiletree.fsstorage.FSStorageManager()
	renderer = tiletree.NullRenderer()
	cutter = tiletree.NullGeomCutter()
	generator = tiletree.QuadTreeGenerator()
	generator.generate(0, 0, 10, 10, storage_manager, renderer, cutter, num_levels=5)

def null_csv_tree_test():
	storage_manager = tiletree.csvstorage.CSVStorageManager(open('tree.csv','w'), None)
	renderer = tiletree.NullRenderer()
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	generator = tiletree.QuadTreeGenerator()
	min_x, min_y, max_x, max_y = cutter.bbox()
	generator.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=15)

def shapefile_cutter_test():
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	print cutter.geom.area, cutter.geom.bounds
	geom = cutter.cut(-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	print geom.area, geom.bounds

def mapserver_render_test():
	#storage_manager = tiletree.fsstorage.FSStorageManager()
	storage_manager = tiletree.csvstorage.CSVStorageManager(open('tree.csv','w'), open('images.csv','w'))
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	renderer = tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),['poly_fill'], img_w=256, img_h=256)
	generator = tiletree.QuadTreeGenerator()
	min_x, min_y, max_x, max_y = cutter.bbox()
	generator.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=15)

def pil_render_test():
	storage_manager = tiletree.csvstorage.CSVStorageManager(open('tree.csv','w'), open('images.csv','w'))
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	renderer = tiletree.pil.PILRenderer()
	#renderer = tiletree.NullRenderer()
	generator = tiletree.QuadTreeGenerator()
	min_x, min_y, max_x, max_y = cutter.bbox()
	generator.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=6)

def postgres_test():
	storage_manager = tiletree.postgres.PostgresStorageManager('dbname=planetwoo user=guidek12', 'north_america_tree')
	storage_manager.fetch(0, 0, 0)

def geom_builder_csv_test():
	storage_manager = tiletree.csvstorage.CSVStorageManager(open('tree.csv','w'), None,
			fields=['node_id', 'zoom_level', 'tile_x', 'tile_y',
				'min_x', 'min_y', 'max_x', 'max_y', 'is_leaf', 'is_blank', 'is_full', 'geom'])
	renderer = tiletree.NullRenderer()
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	generator = tiletree.QuadTreeGenerator()
	min_x, min_y, max_x, max_y = cutter.bbox()
	generator.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=8)

def geom_builder_shapefile_test():
	storage_manager = tiletree.shapefile.ShapefileStorageManager('tile_geom.shp', 'tile_geom')
	renderer = tiletree.NullRenderer()
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	generator = tiletree.QuadTreeGenerator()
	min_x, min_y, max_x, max_y = cutter.bbox()
	generator.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=6)

def individual_geom_builder_shapefile_test():
	storage_manager = tiletree.shapefile.IndividualShapefileStorageManager('tile_geom')
	renderer = tiletree.NullRenderer()
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	generator = tiletree.QuadTreeGenerator()
	min_x, min_y, max_x, max_y = cutter.bbox()
	generator.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=6)

def vector_tile_render_test():
	renderer = tiletree.mapserver.MapServerRenderer(open('vector_tiles.map','r').read(),['poly_fill'])
	tiletree.mapserver.render_vector_tiles(renderer, "dbname=planetwoo user=guidek12", "tile_geom", "poly_fill")

def meta_tile_mapserver_test():
	#storage_manager = tiletree.fsstorage.FSStorageManager()
	backend_storage_manager = tiletree.csvstorage.CSVStorageManager(open('tree.csv','w'), open('images.csv','w'))
	storage_manager = tiletree.splitstorage.SplitStorageManager(backend_storage_manager, 3)
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	renderer = tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),['poly_fill'], img_w=256, img_h=256)
	generator = tiletree.QuadTreeGenerator()
	min_x, min_y, max_x, max_y = cutter.bbox()
	generator.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=2)

def main():
	#null_test()
	#null_fs_tree_test()
	#null_csv_tree_test()
	#shapefile_cutter_test()
	#mapserver_render_test()
	#pil_render_test()
	#postgres_test()
	#geom_builder_csv_test()
	#geom_builder_shapefile_test()
	#individual_geom_builder_shapefile_test()
	#vector_tile_render_test()
	meta_tile_mapserver_test()
	pass

if( __name__ == '__main__'):
	main()

