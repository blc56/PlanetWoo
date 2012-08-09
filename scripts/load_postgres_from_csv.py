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

#!/usr/bin/env python
import sys
sys.path.append('../')
import tiletree
import tiletree.postgres
import argparse
import json

def main():
	parser = argparse.ArgumentParser(description="Multithreaded Mapserver Shapfile CSV Tile Renderer")
	parser.add_argument('-c', '--conn-str', dest='conn_str', required=True, action='store',
		help='Postgres database connection string')
	parser.add_argument('-C', '--create', dest='create', required=False, action='store_true',
		help='Drop and recreate tables')
	parser.add_argument('-t', '--tree', dest='tree', required=True, help='Path to tree .csv file')
	parser.add_argument('-i', '--images', dest='images', required=True, help='Path to images .csv file')
	parser.add_argument('-tt', '--tree-table', dest='tree_table', required=True,
			help='Name of postgres tree table')
	parser.add_argument('-it', '--images-table', dest='images_table', required=True,
			help='Name of postgres image table')
	args = parser.parse_args()
	
	storage_manager = tiletree.postgres.PostgresStorageManager(args.conn_str, args.tree_table, args.images_table)
	if(args.create):
		storage_manager.recreate_tables()
	storage_manager.copy(open(args.tree, 'r'), open(args.images, 'r'))

if(__name__ == '__main__'):
	main()

