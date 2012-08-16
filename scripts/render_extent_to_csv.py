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

from batch_render_to_csv import *

def main():
	parser = argparse.ArgumentParser(description="Multithreaded Mapserver Shapfile CSV Tile Renderer")
	parser.add_argument('-c', '--config', dest='config', required=True, help='Path to configuration json file')
	parser.add_argument('-e', '--extent', dest='extent', type=float, required=True, nargs='+', help="<minx> <miny> <maxx> <maxy>")
	parser.add_argument('-b', '--batch', dest='batch', required=False, action='store_true', help="Call batch renderer?")
	args = parser.parse_args()

	if(len(args.extent) != 4):
		raise Exception("Invalid extent!")

	config = json.loads(open(args.config, 'r').read())
	tile_coords = tiletree.extent_to_tile_coord(args.extent, config['map_extent'])
	print 'Root Tile Coordinate:', tile_coords
	config['dist_render']['start_zoom'] = tile_coords[0]
	config['dist_render']['start_tile_x'] = tile_coords[1]
	config['dist_render']['start_tile_y'] = tile_coords[2]

	if(args.batch):
		do_batch(config)
	else:
		render_to_csv(config)

if(__name__ == '__main__'):
	main()

