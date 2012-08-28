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

##\file dist_render.py Fabric script for distributed rendering
from fabric.api import serial, parallel, task, local, settings, abort, run, cd, env, get, put, execute, sudo, hide
import json
import sys
sys.path.append('../')
import tiletree
import tiletree.postgres
import os.path
import math
import uuid
import StringIO
import copy
import time

def split_bbox(min_num_boxes, start_zoom, start_tile_x, start_tile_y, stop_zoom, min_x, min_y, max_x, max_y):
	nodes = [tiletree.QuadTreeGenNode(None, min_x, min_y, max_x, max_y, start_zoom, tile_x=start_tile_x,
		tile_y=start_tile_y)]
	this_zoom = start_zoom

	while(len(nodes) < min_num_boxes and this_zoom <= stop_zoom):
		new_nodes = []
		for node in nodes:
			new_nodes.extend(node.split())
		nodes = new_nodes
		this_zoom +=1

	return nodes

def create_machine_jobs(global_config):
	dist_render_config = global_config['dist_render']

	#override parameteres with render_extent if necessary
	render_extent = global_config['map_extent']
	if('render_extent' in dist_render_config):
		render_extent = dist_render_config['render_extent']
		tile_coords = tiletree.extent_to_tile_coord(render_extent, global_config['map_extent'])
		print 'Root Tile Coordinate:', tile_coords
		dist_render_config['start_zoom'] = tile_coords[0]
		dist_render_config['start_tile_x'] = tile_coords[1]
		dist_render_config['start_tile_y'] = tile_coords[2]
		#get the extent of the root node
		render_extent = tiletree.tile_coord_to_bbox(tile_coords[0], tile_coords[1], tile_coords[2],
				global_config['map_extent'])


	total_num_threads = sum(x['num_threads'] for x in dist_render_config['render_nodes'])
	min_num_jobs = dist_render_config.get('min_num_jobs', 1)
	if(total_num_threads > min_num_jobs):
		min_num_jobs = total_num_threads
	map_extent = global_config['map_extent']

	jobs = split_bbox(min_num_jobs, dist_render_config['start_zoom'],
			dist_render_config['start_tile_x'], dist_render_config['start_tile_y'],
			dist_render_config['stop_zoom'], *render_extent)

	fill_to_zoom_level = jobs[0].zoom_level - 1

	jobs_per_thread = int(math.ceil(len(jobs) / float(total_num_threads)))

	render_node_configs = {}
	for render_node in dist_render_config['render_nodes']:
		this_num_jobs = min(jobs_per_thread * render_node['num_threads'], len(jobs))
		#inherit the stuff from the global config
		this_config = copy.copy(global_config)
		this_config.update({
			'address': render_node['address'],
			'num_threads': render_node['num_threads'],
			'jobs': []
		})
		for job in jobs[0:this_num_jobs]:
			this_config['jobs'].append({
				'extent': [job.min_x, job.min_y, job.max_x, job.max_y],
				'start_zoom': job.zoom_level,
				'stop_zoom': dist_render_config['stop_zoom'],
				'tile_x':job.tile_x,
				'tile_y':job.tile_y,
			})
		del jobs[0:this_num_jobs]
		render_node_configs[render_node['address']] = this_config

	#add in any left over bits at the top of the tree
	if(fill_to_zoom_level >= dist_render_config['start_zoom']):
		render_node_configs.values()[0]['jobs'].append({
			'extent': global_config['map_extent'],
			'start_zoom': dist_render_config['start_zoom'],
			'stop_zoom': fill_to_zoom_level,
			'tile_x': dist_render_config['start_tile_x'],
			'tile_y': dist_render_config['start_tile_y'],
		})

	#print json.dumps(render_node_configs)

	return render_node_configs

@task
@parallel
def update_planetwoo(prefix="/opt/planetwoo"):
	with cd('%s/PlanetWoo/' % prefix):
		sudo('git pull')
@parallel
def copy_data_files(render_node_config):
	#copy over mapfile, shapefile, and render config files
	data_file_dest =  render_node_config['dist_render']['data_file_dest']
	sudo('mkdir -p %s' % data_file_dest)
	sudo('chown %(user)s:%(user)s %(path)s' % {'user':env.user, 'path':data_file_dest})

	for layer_name in render_node_config['layer_order']:
		layer_config = render_node_config['layers'][layer_name]
		for file_type in ['mapfile_path', 'shapefile_path']:
			if(file_type in layer_config):
				local_path = layer_config[file_type]
				if(file_type == 'shapefile_path'):
					shapefile_root = os.path.splitext(local_path)[0]
					put(shapefile_root + '.*', data_file_dest)
				else:
				    put(local_path, data_file_dest)

	tmp_config_bytes = StringIO.StringIO()
	tmp_config_bytes.write(json.dumps(render_node_config))
	tmp_file_name = str(uuid.uuid4()) + '.json'

	remote_file_path = os.path.join(data_file_dest, tmp_file_name)
	put(tmp_config_bytes, remote_file_path)
	return remote_file_path

@parallel
def run_render_node(render_node_configs):
	render_node_config = render_node_configs[env.host]
	#for some reason it isn't picking up the username from host strings so I manually override it here
	#ugh!
	host_parts = render_node_config['address'].split('@')
	if(len(host_parts) == 2):
		env.user=host_parts[0]

	#update_planetwoo()
	remote_config_path = copy_data_files(render_node_config)

	run("dtach -n /tmp/tiletree bash -l -c '%s -c %s'" % (render_node_config['dist_render']['render_script'], remote_config_path))
	#run("bash -l -c '%s -c %s'" % (render_node_config['render_script'], remote_config_path))

def render_helper(global_config):
	render_node_configs = create_machine_jobs(global_config)
	render_hosts = [n['address'] for n in render_node_configs.values()]
	execute(run_render_node, hosts=render_hosts, render_node_configs=render_node_configs)

@task
@serial
def render(config_path, layer_order=None):
	global_config=json.loads(open(config_path, 'r').read())

	if(layer_order != None):
		print layer_order
		global_config['layer_order'] = json.loads(layer_order)

	render_helper(global_config)

def get_progress_from_host(render_node_configs):
	output_prefix = render_node_configs[env.host_string]['dist_render']['output_prefix']
	num_jobs = len(render_node_configs[env.host_string]['jobs'])
	host_stats = []
	for x in range(num_jobs):
		log_file = output_prefix + ('render_%d.log' % x)
		host_stats.append(run('tail -n 1 %s' % log_file))
	return host_stats

@parallel
def get_node_results(global_config, render_node_configs, download_path="./"):
	output_prefix = global_config['dist_render']['output_prefix']
	num_jobs = len(render_node_configs[env.host_string]['jobs'])
	host_stats = []
	for x in range(num_jobs):
		local('mkdir -p %s' % env.host)
		get(output_prefix + '*.csv', env.host)
		get(output_prefix + '*.log', env.host)
	return host_stats

def get_results_helper(global_config, download_path="./"):
	render_node_configs = create_machine_jobs(global_config)
	render_hosts = [n['address'] for n in render_node_configs.values()]
	execute(get_node_results, global_config, render_node_configs, download_path=download_path, hosts=render_hosts)

@task
@serial
def get_results(config_path, download_path="./"):
	global_config=json.loads(open(config_path, 'r').read())
	get_results_helper(global_config, download_path=download_path)

@task
@serial
def batch_load_results(config_path, connect_str, download_dir,
		address_override=None, prefix_override=None):
	#TODO: FIXME XXX: convert this function for new config file format
	global_config=json.loads(open(config_path, 'r').read())
	render_node_configs = create_machine_jobs(global_config)

	for layer_name in global_config['layer_order']:
		is_first_load = True
		layer = global_config['layers'][layer_name]
		node_table = layer['tree_table']
		image_table = layer['image_table']
		storage = tiletree.postgres.PostgresStorageManager(connect_str, node_table, image_table)
		for render_node in render_node_configs.values():
			if(is_first_load):
				print 'Create tables.', node_table, image_table
				is_first_load = False
				storage.recreate_tables()
			for x in range(0, len(render_node['jobs'])):
				prefix = prefix_override
				if(prefix_override == None):
					prefix = os.path.basename(layer['output_prefix'])
				address = address_override
				if(address_override == None):
					address = render_node['address']
				tree_path = os.path.join(download_dir, address) + '/' + prefix + 'tree_%d.csv' % x
				image_path = os.path.join(download_dir, address) + '/' + prefix + 'images_%d.csv' % x
				print tree_path, image_path
				storage.copy(open(tree_path, 'r'), open(image_path, 'r'))
				storage.flush()

@task
@serial
def dump_progress(config_path):
	global_config=json.loads(open(config_path, 'r').read())
	render_node_configs = create_machine_jobs(global_config)
	render_hosts = [n['address'] for n in render_node_configs.values()]
	stats = execute(get_progress_from_host, render_node_configs, hosts=render_hosts)
	for host in stats:
		for x in range(len(stats[host])):
			print host + ',', str(x) + ':', stats[host][x]

@task
@serial
def watch_progress(config_path):
	with hide('status', 'running', 'stdout'):
		while(True):
			print '==========================='
			dump_progress(config_path)
			time.sleep(5)

