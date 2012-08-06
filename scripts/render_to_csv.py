#!/usr/bin/env python
import sys
sys.path.append('../')
import tiletree
import tiletree.csvstorage
import tiletree.shapefile
import tiletree.mapserver
import tiletree.postgres
import tiletree.label
import tiletree.multi
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
	elif(cutter_type == 'multi'):
		return tiletree.multi.MultiCutter([load_cutter(c) for c in config['cutters']])
	else:
		return tiletree.NullGeomCutter()

def load_label_classes(layer_config, label_renderer):
	for layer_name, label_classes in layer_config['label_classes'].items():
		for label_class_dict in label_classes:
			label_class = tiletree.label.LabelClass()
			label_class.from_dict(label_class_dict)
			label_renderer.add_label_class(layer_name, label_class)

def load_storage_manager(config, job_id):
	storage_type = config.get('storage_type', 'csv')
	if(storage_type == 'csv'):
		tree_file_path = config['output_prefix'] + 'tree_%d.csv' % job_id
		image_file_path = config['output_prefix'] + 'images_%d.csv' % job_id
		return tiletree.csvstorage.CSVStorageManager(open(tree_file_path, 'w'), open(image_file_path, 'w'))
	elif(storage_type == 'multi'):
		return tiletree.multi.MultiStorageManager([load_storage_manager(c, job_id) for c in config['storage_managers']])

def load_renderer(config):
	renderer_type = config.get('renderer_type', 'mapserver')

	if(renderer_type == 'mapserver'):
		return tiletree.mapserver.MapServerRenderer(open(config['mapfile_path'],'r').read(),
			config['mapserver_layers'], img_w=256, img_h=256, img_buffer=config.get('img_buffer', 0),
			min_zoom=config.get('min_zoom', 0), max_zoom=config.get('max_zoom', 20),
			cache_fulls=config.get('cache_fulls', True))

	elif(renderer_type == 'label'):
		renderer = tiletree.label.LabelRenderer(open(config['mapfile_path'],'r').read(),
			config.get('label_col_index', None), config['mapserver_layers'],
			config.get('min_zoom', 0), config.get('max_zoom', 100),
			point_labels=config.get('point_labels', False))
		load_label_classes(config, renderer)
		return renderer

	elif(renderer_type == 'multi'):
		return tiletree.multi.MultiRenderer([load_renderer(c) for c in config['renderers']])

	return None

def load_postgres_cutter(connect_str, table_name):
	return tiletree.postgres.PostgresCutter(connect_str, table_name)

def load_shapefile_cutter(shapefile_path, shapefile_layer):
	return  tiletree.shapefile.ShapefileCutter(shapefile_path, str(shapefile_layer))

def load_maptree_cutter(shapefile_path, shapefile_layer):
	shapefile_root = os.path.basename(shapefile_path)
	qix_path = shapefile_root + '.qix'
	return tiletree.shapefile.MaptreeCutter(shapefile_path, str(shapefile_layer), qix_path)

def load_shapefile(config):
	if(not config.get('load_shapefile_to_postgres',False)):
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
		log_file = open(config['output_prefix'] + 'render_%d.log' % count, 'w')
		start_checks_zoom = config.get('start_checks_zoom', None)
		check_full = config.get('check_full', True)
		renderer = load_renderer(config)
		storage_manager = load_storage_manager(config, count)
				
		start_node = tiletree.QuadTreeGenNode(min_x=job['extent'][0], min_y=job['extent'][1],
			max_x=job['extent'][2], max_y=job['extent'][3], zoom_level=job['start_zoom'],
			tile_x=job['tile_x'], tile_y=job['tile_y'])
		generate_jobs.append(start_node.to_generator_job(
			storage_manager,
			renderer,
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

