#!/usr/bin/env python
import sys
sys.path.append('../')
import tiletree
import tiletree.csvstorage
import tiletree.shapefile
import tiletree.mapserver
import tiletree.postgres
import os.path
import argparse
import json
import subprocess

def load_cutter(config):
	cutter_type = config['cutter_type']
	if(cutter_type == 'shapefile'):
		return load_shapefile_cutter(config['shapefile_path'], config['shapefile_layer'])
	elif(cutter_type == 'maptree'):
		return load_maptree_cutter(config['shapefile_path'], config['shapefile_layer'])
	elif(cutter_type == 'postgres'):
		return load_postgres_cutter(config['connect_string'], config['table_name'])
	else:
		return tiletree.NullGeomCutter()

def load_postgres_cutter(connect_str, table_name):
	return tiletree.postgres.PostgresCutter(connect_str, table_name)

def load_shapefile_cutter(shapefile_path, shapefile_layer):
	return  tiletree.shapefile.ShapefileCutter(shapefile_path, str(shapefile_layer))

def load_maptree_cutter(shapefile_path, shapefile_layer):
	shapefile_root = os.path.basename(shapefile_path)
	qix_path = shapefile_root + '.qix'
	return tiletree.shapefile.MaptreeCutter(shapefile_path, str(shapefile_layer), qix_path)

def load_shapefile(config):
	if(not config['load_shapefile_to_postgres']):
		return
	else:
		subprocess.call(\
				'%(prefix)sogr2ogr -f "PostgreSQL" "PG: %(conn_str)s" %(shp_path)s -nlt GEOMETRY %(shp_layer)s -overwrite -lco PRECISION=no' %\
			{'conn_str':config['connect_string'], 'shp_path':config['shapefile_path'],
			'shp_layer': config['shapefile_layer'], 'prefix':config['ogr_prefix']}, shell=True)

def render_to_csv(config):
	generate_jobs = []
	count = 0

	print "Loading shapefile."
	load_shapefile(config)
	print "Loading cutter."
	cutter = load_cutter(config)

	print "Creating jobs."
	for job in config['jobs']:
		tree_file_path = config['output_prefix'] + 'tree_%d.csv' % count
		image_file_path = config['output_prefix'] + 'images_%d.csv' % count
		log_file = open(config['output_prefix'] + 'render_%d.log' % count, 'w')
		start_checks_zoom = config.get('start_checks_zoom', None)
		check_full = config.get('check_full', True)
				
		start_node = tiletree.QuadTreeGenNode(min_x=job['extent'][0], min_y=job['extent'][1],
			max_x=job['extent'][2], max_y=job['extent'][3], zoom_level=job['start_zoom'],
			tile_x=job['tile_x'], tile_y=job['tile_y'])
		generate_jobs.append(start_node.to_generator_job(
			tiletree.csvstorage.CSVStorageManager(open(tree_file_path, 'w'), open(image_file_path, 'w')),
			tiletree.mapserver.MapServerRenderer(open(config['mapfile_path'],'r').read(),
				config['mapserver_layers'], img_w=256, img_h=256),
			cutter.clone(),
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

