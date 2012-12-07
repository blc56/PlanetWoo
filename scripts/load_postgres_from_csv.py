#!/usr/bin/env python
#Copyright (C) 2012 Excensus, LLC.
#
#This file is part of PlanetWoo.
#
#PlanetWoo is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#PlanetWoo is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with PlanetWoo.  If not, see <http://www.gnu.org/licenses/>.

import sys
import planetwoo.tiletree as tiletree
import planetwoo.tiletree.postgres as postgres
import argparse
import json

def main():
	parser = argparse.ArgumentParser(description="Multithreaded Mapserver Shapfile CSV Tile Renderer")
	parser.add_argument('-c', '--conn-str', dest='conn_str', required=True, action='store',
		help='Postgres database connection string')
	parser.add_argument('-C', '--create', dest='create', required=False, action='store_true',
		help='Force Drop and recreate tables')
	parser.add_argument('-t', '--tree', dest='tree', nargs='+', required=False, help='Path to tree .csv file', default=[])
	parser.add_argument('-i', '--images', dest='images', nargs='+', required=False, help='Path to images .csv file', default=[])
	parser.add_argument('-tt', '--tree-table', dest='tree_table', required=True,
			help='Name of postgres tree table')
	parser.add_argument('-it', '--images-table', dest='images_table', required=True,
			help='Name of postgres image table')
	parser.add_argument('-e', '--clear-extent', dest='clear_extent', required=False, nargs='+',
			help='Extent to clear. Requires -m', type=float)
	parser.add_argument('-m', '--map-extent', dest='map_extent', required=False, nargs='+',
			help='Map extent.', type=float)
	args = parser.parse_args()
	
	storage_manager = postgres.PostgresStorageManager(args.conn_str, args.tree_table, args.images_table)

	if(args.create or not storage_manager.do_tables_exist()):
		print "Creating tables"
		storage_manager.recreate_tables()

	if(args.clear_extent):
		if(args.map_extent == None):
			raise Exception("--map-extent must be specified with --clear-extent")
		if(len(args.clear_extent) != 4):
			raise Exception("--clear-extent must have 4 arguments")
		if(len(args.map_extent) != 4):
			raise Exception("--map-extent must have 4 arguments")

		print "Clearing Extent"
		storage_manager.clear_extent(args.clear_extent, args.map_extent)


	if(len(args.tree) > 0 and len(args.images) > 0):
		if(len(args.tree) != len(args.images)):
			raise Exception("You must specify the same number of tree and image csv files")
		for tree, image in zip(args.tree, args.images):
			print "Now loading:", tree, image
			storage_manager.copy(open(tree, 'r'), open(image, 'r'))

	print "Committing"
	storage_manager.flush()

if(__name__ == '__main__'):
	main()

