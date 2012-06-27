##\file dist_render.py Fabric script for distributed rendering
from fabric.api import serial, parallel, task, local, settings, abort, run, cd, env, get, put, execute, sudo, hide
import json
import sys
sys.path.append('../')
import tiletree
import os.path
import math
import uuid
import StringIO
import copy
import time

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

	render_node_configs = {}
	for render_node in global_config['render_nodes']:
		this_num_jobs = min(jobs_per_thread * render_node['num_threads'], len(jobs))
		#inherit the stuff from the global config
		this_config = copy.copy(global_config)
		this_config.update({
			'address': render_node['address'],
			'num_threads': render_node['num_threads'],
			'mapfile_path': mapfile_path,
			'shapefile_path': shapefile_path,
			'local_shapefile_path':global_config['shapefile_path'],
			'local_mapfile_path':global_config['mapfile_path'],
			#'output_prefix': global_config['output_prefix'],
			#'shapefile_layer':  global_config['shapefile_layer'],
			#'mapserver_layers': global_config['mapserver_layers'],
			'jobs': []
		})
		for job in jobs[0:this_num_jobs]:
			this_config['jobs'].append({
				'extent': [job.min_x, job.min_y, job.max_x, job.max_y],
				'start_zoom': job.zoom_level,
				'stop_zoom': global_config['stop_zoom'],
			})
		del jobs[0:this_num_jobs]
		render_node_configs[render_node['address']] = this_config

	#add in any left over bits at the top of the tree
	if(fill_to_zoom_level >= 0):
		render_node_configs.values()[0]['jobs'].append({
			'extent': global_config['map_extent'],
			'start_zoom': global_config['start_zoom'],
			'stop_zoom': fill_to_zoom_level
		})

	#print json.dumps(render_node_configs)

	return render_node_configs

@parallel
def update_planetwoo(prefix="/opt/planetwoo"):
	with cd('%s/PlanetWoo/' % prefix):
		sudo('git pull')
@parallel
def copy_data_files(render_node_config):
	#copy over mapfile, shapefile, and render config files
	sudo('mkdir -p %s' % render_node_config['data_file_dest'])
	sudo('chown %(user)s:%(user)s %(path)s' % {'user':env.user, 'path':render_node_config['data_file_dest']})
	put(render_node_config['local_mapfile_path'], render_node_config['data_file_dest'])
	shapefile_root = os.path.splitext(render_node_config['local_shapefile_path'])[0]
	put(shapefile_root + '.*', render_node_config['data_file_dest'])

	tmp_config_bytes = StringIO.StringIO()
	tmp_config_bytes.write(json.dumps(render_node_config))
	tmp_file_name = str(uuid.uuid4()) + '.json'

	remote_file_path = os.path.join(render_node_config['data_file_dest'], tmp_file_name)
	put(tmp_config_bytes, remote_file_path)
	return remote_file_path

@parallel
def run_render_node(render_node_configs):
	update_planetwoo()
	render_node_config = render_node_configs[env.host]
	remote_config_path = copy_data_files(render_node_config)

	run("dtach -n /tmp/tiletree bash -l -c '%s -c %s'" % (render_node_config['render_script'], remote_config_path))
	#run("bash -l -c '%s -c %s'" % (render_node_config['render_script'], remote_config_path))


@task
@serial
def render(config_path):
	global_config=json.loads(open(config_path, 'r').read())
	render_node_configs = create_machine_jobs(global_config)
	render_hosts = [n['address'] for n in render_node_configs.values()]
	#for some reason it isn't picking up the username from host strings so I manually override it here
	#ugh!
	env.user = 'ubuntu'
	execute(run_render_node, hosts=render_hosts, render_node_configs=render_node_configs)

def get_progress_from_host(render_node_configs):
	output_prefix = render_node_configs[env.host_string]['output_prefix']
	num_jobs = len(render_node_configs[env.host_string]['jobs'])
	host_stats = []
	for x in range(num_jobs):
		log_file = output_prefix + ('render_%d.log' % x)
		#host_stats.append(tiletree.parse_stats_line(run('tail -n 1 %s' % log_file)))
		host_stats.append(run('tail -n 1 %s' % log_file))
	return host_stats


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
