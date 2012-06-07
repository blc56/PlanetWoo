#!/usr/bin/env python
import sys
sys.path.append('../../')
import tiletree
import tiletree.fsstorage
import tiletree.csvstorage
import tiletree.mapserver
import tiletree.shapefile

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
	generator.generate(0, 0, 20, 20, storage_manager, renderer, cutter, num_levels=5)

def shapefile_test():
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	print cutter.geom.area, cutter.geom.bounds
	geom = cutter.cut(-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	print geom.area, geom.bounds

def mapserver_render_test():
	storage_manager = tiletree.csvstorage.CSVStorageManager(open('tree.csv','w'), open('images.csv','w'))
	#storage_manager = tiletree.fsstorage.FSStorageManager()
	renderer = tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),'poly_fill')
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/united_states_merged.shp', 'united_states_merged')
	generator = tiletree.QuadTreeGenerator()
	generator.generate(-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803, storage_manager, renderer, cutter, num_levels=5)

def main():
	#null_fs_tree_test()
	#null_csv_tree_test()
	#shapefile_test()
	mapserver_render_test()

if( __name__ == '__main__'):
	main()

