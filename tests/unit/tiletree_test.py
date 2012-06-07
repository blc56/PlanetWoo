#!/usr/bin/env python
import sys
sys.path.append('../../')
import tiletree
import tiletree.fsstorage
import tiletree.csvstorage
import tiletree.mapserver

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

def mapserver_render_test():
	#storage_manager = tiletree.csvstorage.CSVStorageManager(open('tree.csv','w'), open('images.csv','w'))
	storage_manager = tiletree.fsstorage.FSStorageManager()
	renderer = tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),'poly_fill')
	cutter = tiletree.NullGeomCutter()
	generator = tiletree.QuadTreeGenerator()
	generator.generate(0, 0, 20, 20, storage_manager, renderer, cutter, num_levels=4)

def main():
	null_fs_tree_test()
	null_csv_tree_test()
	#mapserver_render_test()

if( __name__ == '__main__'):
	main()

