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

import copy
import gc
import mapscript

from render_to_csv import *

def do_batch(config):
	for batch in config['batch_render']:
		new_config = copy.copy(config)
		new_config.update(batch)
		print "Now running:", batch
		render_to_csv(new_config)
		mapscript.msCleanup()

def main():
	parser = argparse.ArgumentParser(description="Multithreaded Mapserver Shapfile CSV Tile Renderer")
	parser.add_argument('-c', '--config', dest='config', required=True, help='Path to configuration json file')
	parser.add_argument('-p', '--prefix', dest='prefix', required=False, help='Additional prefix for output files.', default='')
	args = parser.parse_args()

	config = json.loads(open(args.config, 'r').read())
	config['run_prefix'] = args.prefix
	do_batch(config)


if(__name__ == '__main__'):
	main()

