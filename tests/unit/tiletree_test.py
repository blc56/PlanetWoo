#!/usr/bin/env python
import sys
sys.path.append('../../')
import tiletree

def null_fs_tree_test():
	storage_manager = tiletree.FSStorageManager()
	renderer = tiletree.NullRenderer()
	cutter = tiletree.GeomCutter()
	generator = tiletree.QuadTreeGenerator()
	generator.generate(0, 0, 10, 10, storage_manager, renderer, cutter, num_levels=5)

def null_csv_tree_test():
	storage_manager = tiletree.CSVStorageManager(open('tree.csv','w'), open('images.csv','w'))
	renderer = tiletree.NullRenderer()
	cutter = tiletree.GeomCutter()
	generator = tiletree.QuadTreeGenerator()
	generator.generate(0, 0, 20, 20, storage_manager, renderer, cutter, num_levels=5)

def mapserver_render_test():
	#storage_manager = tiletree.CSVStorageManager(open('tree.csv','w'), open('images.csv','w'))
	storage_manager = tiletree.FSStorageManager()
	renderer = tiletree.MapServerRenderer(open('default.map','r').read(),'poly_fill')
	cutter = tiletree.GeomCutter()
	generator = tiletree.QuadTreeGenerator()
	generator.generate(0, 0, 20, 20, storage_manager, renderer, cutter, num_levels=4)

def main():
	#null_fs_tree_test()
	#null_csv_tree_test()
	mapserver_render_test()

if( __name__ == '__main__'):
	main()

