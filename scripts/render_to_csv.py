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
import planetwoo.tiletree.csvstorage
import planetwoo.tiletree.shapefile
import planetwoo.tiletree.mapserver
import planetwoo.tiletree.postgres
import planetwoo.tiletree.label
import planetwoo.tiletree.multi
import os.path
import argparse
import json
import subprocess


def render_to_csv(config, ):
	generate_jobs = []
	count = 0
	log_prefix= config.get('log_prefix','render_')

	print "Creating jobs."
	for job in config['jobs']:
		prefix = config['dist_render']['output_prefix'] + log_prefix
		prefix += config.get('run_prefix', '')
		log_file = open(prefix + log_prefix + ('%d.log' % count), 'w')
		start_checks_zoom = config.get('start_checks_zoom', None)
		check_full = config.get('check_full', True)

		#this can happen when an individual batch uses "stop_zoom" 
		if(config['stop_zoom'] < job['stop_zoom']):
			job['stop_zoom'] = config['stop_zoom']

		#this can happen when an individual batch uses "stop_zoom" 
		if(job['start_zoom'] > job['stop_zoom']):
			print 'Skipping job due to stop zoom'
			continue
				
		start_node = tiletree.QuadTreeGenNode(min_x=job['extent'][0], min_y=job['extent'][1],
			max_x=job['extent'][2], max_y=job['extent'][3], zoom_level=job['start_zoom'],
			tile_x=job['tile_x'], tile_y=job['tile_y'])
		print start_node
		generate_jobs.append(start_node.to_generator_job(
			count,
			config,
			job['stop_zoom'],
			log_file,
			start_checks_zoom,
			check_full)
		)

		count += 1

	print "Running."
	tiletree.generate_mt(generate_jobs, num_threads=config['num_threads'])

def main():
	parser = argparse.ArgumentParser(description="Multithreaded Mapserver Shapfile CSV Tile Renderer")
	parser.add_argument('-c', '--config', dest='config', required=True, help='Path to configuration json file')
	args = parser.parse_args()

	config = json.loads(open(args.config, 'r').read())

	render_to_csv(config)

if(__name__ == '__main__'):
	main()

