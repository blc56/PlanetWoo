#!/usr/bin/env python
import sys
sys.path.append('../')
import tiletree
import tiletree.csvstorage
import tiletree.shapefile
import tiletree.mapserver
import os.path
import argparse
import json

def render_to_csv(mapfile_path, mapserver_layers, shapefile_path, shapefile_layer, output_prefix, num_threads, jobs):
	generate_jobs = []
	count = 0
	cutter = tiletree.shapefile.ShapefileCutter(shapefile_path, str(shapefile_layer))
	for job in jobs:
		tree_file_path = output_prefix + 'tree_%d.csv' % count
		image_file_path = output_prefix + 'images_%d.csv' % count
		log_file = open(output_prefix + 'render_%d.log' % count, 'w')
				
		start_node = tiletree.QuadTreeGenNode(min_x=job['extent'][0], min_y=job['extent'][1],
			max_x=job['extent'][2], max_y=job['extent'][3], zoom_level=job['start_zoom'])
		generate_jobs.append(start_node.to_generator_job(
			tiletree.csvstorage.CSVStorageManager(open(tree_file_path, 'w'), open(image_file_path, 'w')),
			tiletree.mapserver.MapServerRenderer(open(mapfile_path,'r').read(), mapserver_layers,
				img_w=256, img_h=256),
			cutter.clone(),
			job['stop_zoom'],
			log_file)
		)

		count += 1

	tiletree.generate_mt(generate_jobs, num_threads=num_threads)

def main():
	parser = argparse.ArgumentParser(description="Multithreaded Mapserver Shapfile CSV Tile Renderer")
	parser.add_argument('-c', '--config', dest='config', required=True, help='Path to configuration json file')
	args = parser.parse_args()

	config = json.loads(open(args.config, 'r').read())

	render_to_csv(config['mapfile_path'], config['mapserver_layers'],
			config['shapefile_path'], config['shapefile_layer'], config['output_prefix'],
			config['num_threads'], config['jobs'])

if(__name__ == '__main__'):
	main()

