#!/usr/bin/env python
import sys
sys.path.append('../../')
import tiletree
import tiletree.fsstorage
import tiletree.csvstorage
import tiletree.mapserver
import tiletree.shapefile
import tiletree.postgres

def null_fs_tree_test():
	storage_manager = tiletree.fsstorage.FSStorageManager()
	renderer = tiletree.NullRenderer()
	cutter = tiletree.NullGeomCutter()
	generator = tiletree.QuadTreeGenerator()
	generator.generate(0, 0, 10, 10, storage_manager, renderer, cutter, num_levels=5)

def null_csv_tree_test():
	storage_manager = tiletree.csvstorage.CSVStorageManager(open('tree.csv','w'), open('images.csv','w'))
	renderer = tiletree.NullRenderer()
	cutter = tiletree.NullGeomCutter()
	generator = tiletree.QuadTreeGenerator()
	generator.generate(0, 0, 20, 20, storage_manager, renderer, cutter, num_levels=7)

def shapefile_test():
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	print cutter.geom.area, cutter.geom.bounds
	geom = cutter.cut(-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	print geom.area, geom.bounds

def mapserver_render_test():
	#storage_manager = tiletree.fsstorage.FSStorageManager()
	storage_manager = tiletree.csvstorage.CSVStorageManager(open('tree.csv','w'), open('images.csv','w'))
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	renderer = tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),'poly_fill',
			'test_geo/webmerc_northamerica/north_america.shp')
	generator = tiletree.QuadTreeGenerator()
	min_x, min_y, max_x, max_y = cutter.bbox()
	generator.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=6)

def postgres_test():
	storage_manager = tiletree.postgres.PostgresStorageManager('dbname=planetwoo user=guidek12', 'north_america_tree')
	storage_manager.fetch(0, 0, 0)

def main():
	#null_fs_tree_test()
	#null_csv_tree_test()
	#shapefile_test()
	mapserver_render_test()
	#postgres_test()
	pass

if( __name__ == '__main__'):
	main()

