##\file __init__.py Main classes for the tiletree module. 
from fabric.api import serial, parallel, task, local, settings, abort, run, cd, env, get, put, execute
import json
import sys
sys.path.append('../')
import tiletree
import os.path
import math

def split_bbox(min_num_boxes, start_zoom, stop_zoom, min_x, min_y, max_x, max_y):
	nodes = [tiletree.QuadTreeGenNode(None, min_x, min_y, max_x, max_y, start_zoom)]
	this_zoom = start_zoom

	while(len(nodes) < min_num_boxes and this_zoom <= stop_zoom):
		new_nodes = []
		for node in nodes:
			new_nodes.extend(node.split())
		nodes = new_nodes
		this_zoom +=1

	return nodes

def create_machine_jobs(global_config):
	total_num_threads = sum(x['num_threads'] for x in global_config['render_nodes'])
	map_extent = global_config['map_extent']

	jobs = split_bbox(total_num_threads, global_config['start_zoom'], global_config['stop_zoom'],
			*global_config['map_extent'])

	fill_to_zoom_level = jobs[0].zoom_level - 1

	mapfile_path = os.path.join(global_config['data_file_dest'],
		os.path.basename(global_config['mapfile_path']))
	shapefile_path = os.path.join(global_config['data_file_dest'],
		os.path.basename(global_config['shapefile_path']))

	jobs_per_thread = int(math.ceil(len(jobs) / float(total_num_threads)))

	render_node_configs = []
	for render_node in global_config['render_nodes']:
		this_num_jobs = min(jobs_per_thread * render_node['num_threads'], len(jobs))
		this_config = {
			'address': render_node['address'],
			'num_threads': render_node['num_threads'],
			'mapfile_path': mapfile_path,
			'shapefile_path': shapefile_path,
			'output_prefix': global_config['output_prefix'],
			'shapefile_layer':  global_config['shapefile_layer'],
			'mapserver_layers': global_config['mapserver_layers'],
			'jobs': []
		}
		for job in jobs[0:this_num_jobs]:
			this_config['jobs'].append({
				'extent': [job.min_x, job.max_x, job.min_y, job.max_y],
				'start_zoom': job.zoom_level,
				'stop_zoom': global_config['stop_zoom'],
			})
		del jobs[0:this_num_jobs]
		render_node_configs.append(this_config)

	#add in any left over bits at the top of the tree
	if(fill_to_zoom_level >= 0):
		render_node_configs[0]['jobs'].append({
			'extent': global_config['map_extent'],
			'start_zoom': global_config['start_zoom'],
			'stop_zoom': fill_to_zoom_level
		})

	print json.dumps(render_node_configs)

	return render_node_configs

@parallel
def copy_data_files(global_config):
	for data_file in global_config['data_files']:
		put(data_file, global_config['data_file_dest'])
	put(global_config['mapfile_path'], global_config['data_file_dest'])

@task
@serial
def render(config_path):
	global_config=json.loads(open(config_path, 'r').read())
	render_node_configs = create_machine_jobs(global_config)
	render_hosts = [n['address'] for n in render_node_configs]

	#execute(copy_data_files, hosts=render_hosts, global_config=global_config)

