#!/usr/bin/python

import sys
sys.path.append('../../')
import tiletree

def null_tree_test():
	storage_manager = tiletree.CSVStorageManager()
	renderer = tiletree.NullRenderer()
	cutter = tiletree.GeomCutter()
	generator = tiletree.QuadTreeGenerator()
	generator.generate(0, 0, 10, 10, storage_manager, renderer, cutter, num_levels=5)

def main():
	null_tree_test()

if( __name__ == '__main__'):
	main()

