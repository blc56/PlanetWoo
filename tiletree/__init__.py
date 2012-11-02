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


##\file __init__.py Main classes for the tiletree module. 
import Image
import ImagePalette
import ImageDraw
import StringIO
import copy
import shapely
import shapely.wkt
import json
import time
import shapely.speedups
import multiprocessing
import sys
import types
import math
import subprocess

#a priori knowledge
ESTIMATED_SAVINGS = .90

#if(shapely.speedups.available):
	#shapely.speedups.enable()
	#print "SPEEDUP?"

def palette_png_bytes(png_bytes):
	pngquant = subprocess.Popen(['pngquant','256'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
	out_bytes = pngquant.communicate(input=png_bytes.getvalue())[0]
	return StringIO.StringIO(out_bytes)

def bbox_to_wkt(min_x, min_y, max_x, max_y):
	return "POLYGON((%(min_x)s %(min_y)s, %(max_x)s %(min_y)s, %(max_x)s %(max_y)s, %(min_x)s %(max_y)s, %(min_x)s %(min_y)s))" % {
		'min_x': min_x,
		'min_y': min_y,
		'max_x': max_x,
		'max_y': max_y,
	}

#find the tile coordinate that completely covers exent
#this isn't very efficient, but I'm Lazy
def extent_to_tile_coord(extent, map_extent):
	ret_node = QuadTreeGenNode(min_x=map_extent[0],min_y=map_extent[1],max_x=map_extent[2],max_y=map_extent[3])
	while(True):
		next_node = None
		new_nodes = ret_node.split()
		for node in new_nodes:
			if(node.min_x <= extent[0] and node.min_y <= extent[1] and node.max_x >= extent[2] and
					node.max_y >= extent[3]):
				next_node = node
				break
		if(next_node != None):
			ret_node = next_node
		else:
			return (ret_node.zoom_level, ret_node.tile_x, ret_node.tile_y)
				
	

def geo_coord_to_img(x, y, img_w, img_h, min_x, min_y, max_x, max_y):
	x_scale = img_w  / float(max_x - min_x)
	y_scale = img_h / float(max_y - min_y)
	x = x - min_x
	y = max_y - y
	
	return (x * x_scale, y * y_scale)

def tile_coord_to_bbox(z, x, y, extent):
	#the size of each tile at zoom level z
	tile_dim = 2**z
	x_size = (extent[2] - extent[0]) / float(tile_dim)
	y_size = (extent[3] - extent[1]) / float(tile_dim)

	min_x = extent[0] + (x_size * x)
	min_y = extent[3] - (y_size * (y + 1))
	max_x = min_x + x_size
	max_y = min_y + y_size

	return (min_x, min_y, max_x, max_y)

class NullGeomCutter:
	def __init__(self):
		pass

	def clone(self):
		return copy.deepcopy(self)

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		#raise Exception("Not implemented")
		return None

def build_node_id(zoom_level, tile_x, tile_y):
		#this node id scheme assumes that we won't have a zoom level
		#over 22
	return (tile_y + (tile_x<<22) + (zoom_level<<(22+22)))

def cut_geom_list(bbox, geoms):
	cut_geoms = []
	for geom in geoms:
		if(geom.intersects(bbox)):
			cut_geoms.append(geom)
	return cut_geoms

def cut_helper(min_x, min_y, max_x, max_y, geom):
	#build a geometry from the bounds
	bbox = shapely.wkt.loads("POLYGON((%(min_x)s %(min_y)s, %(min_x)s %(max_y)s, %(max_x)s  %(max_y)s, %(max_x)s %(min_y)s, %(min_x)s %(min_y)s))" % 
		{'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y})

	if(type(geom) == list or isinstance(geom, types.GeneratorType)):
		geoms = geom
	elif(not hasattr(geom, 'geoms')):
		return bbox.intersection(geom)
	else:
		geoms = geom.geoms

	cut_geoms = cut_geom_list(bbox, geoms)

	if(len(cut_geoms) == 0):
		return None
	return cut_geoms


##\brief A simple, QuadTreeNode
#
class QuadTreeGenNode:
	##\param node_id - integer
	#
	def __init__(self, node_id=None, min_x=0, min_y=0, max_x=0, max_y=0, zoom_level=0,
			image_id=None, is_leaf=False, is_blank=False, is_full=False,
			geom=None,tile_x=0, tile_y=0, metadata='', label_geoms=None):
		if(node_id == None):
			node_id = build_node_id(zoom_level, tile_x, tile_y)
		self.node_id = node_id
		self.min_x = min_x
		self.min_y = min_y
		self.max_x = max_x
		self.max_y = max_y
		self.zoom_level = zoom_level
		if(image_id == None):
			image_id = build_node_id(zoom_level, tile_x, tile_y)
		self.image_id = image_id
		self.is_leaf = is_leaf
		self.is_blank = is_blank
		self.is_full = is_full
		self.geom = geom
		self.tile_x = tile_x
		self.tile_y = tile_y
		self.metadata = metadata
		self.label_geoms = label_geoms

	def __repr__(self):
		return repr(self.__dict__)

	def to_dict(self):
		return copy.copy(self.__dict__)

	def split(self, cutter=NullGeomCutter()):
		this_zoom = self.zoom_level + 1
		min_x0 = self.min_x
		min_y0 = self.min_y
		max_x0 = self.min_x + (self.max_x - self.min_x) / 2.0
		max_y0 = self.min_y + (self.max_y - self.min_y) / 2.0
		tile_x0 = self.tile_x * 2
		tile_y0 = self.tile_y * 2
		geom0 = cutter.cut(min_x0, min_y0, max_x0, max_y0, self.geom)

		min_x1 = max_x0
		min_y1 = self.min_y
		max_x1 = self.max_x
		max_y1 = max_y0
		tile_x1 = self.tile_x * 2 + 1
		tile_y1 = self.tile_y * 2
		geom1 = cutter.cut(min_x1, min_y1, max_x1, max_y1, self.geom)

		min_x2 = self.min_x
		min_y2 = max_y0
		max_x2 = max_x0
		max_y2 = self.max_y
		tile_x2 = self.tile_x * 2
		tile_y2 = self.tile_y * 2 + 1
		geom2 = cutter.cut(min_x2, min_y2, max_x2, max_y2, self.geom)

		min_x3 = max_x0
		min_y3 = max_y0
		max_x3 = self.max_x
		max_y3 = self.max_y
		tile_x3 = self.tile_x * 2 + 1
		tile_y3 = self.tile_y * 2 + 1
		geom3 = cutter.cut(min_x3, min_y3, max_x3, max_y3, self.geom)

		image_id = None
		if(self.is_blank or self.is_full):
			image_id = self.image_id

		#do the tile coordinates slippy map style instead of TMS style
		child0 = QuadTreeGenNode(None, min_x0, min_y0, max_x0, max_y0, this_zoom,
				image_id=image_id, geom=geom0, tile_x=tile_x0, tile_y=tile_y2,
				is_leaf=self.is_leaf, is_blank=self.is_blank, is_full=self.is_full,
				metadata=self.metadata)

		child1 = QuadTreeGenNode(None, min_x1, min_y1, max_x1, max_y1, this_zoom,
				image_id=image_id, geom=geom1, tile_x=tile_x1, tile_y=tile_y3,
				is_leaf=self.is_leaf, is_blank=self.is_blank, is_full=self.is_full,
				metadata=self.metadata)

		child2 = QuadTreeGenNode(None, min_x2, min_y2, max_x2, max_y2, this_zoom,
				image_id=image_id, geom=geom2, tile_x=tile_x2, tile_y=tile_y0,
				is_leaf=self.is_leaf, is_blank=self.is_blank, is_full=self.is_full,
				metadata=self.metadata)

		child3 = QuadTreeGenNode(None, min_x3, min_y3, max_x3, max_y3, this_zoom,
				image_id=image_id, geom=geom3, tile_x=tile_x3, tile_y=tile_y1,
				is_leaf=self.is_leaf, is_blank=self.is_blank, is_full=self.is_full,
				metadata=self.metadata)

		return (child0, child1, child2, child3)
		

	def to_json(self):
		self_dict = self.to_dict()
		if(self.geom):
			self_dict['geom'] = shapely.wkt.dumps(self.geom)
		return json.dumps(self_dict)

	def from_json(self, json_str):
		self.__dict__.update(json.loads(json_str))
		if(self.geom):
			self.geom = shapely.wkt.loads(self.geom)

	def to_generator_job(self, count, config, stop_level, log_file=sys.stdout,
			start_checks_zoom=None, check_full=True):
		return GeneratorJob(self.min_x, self.min_y, self.max_x, self.max_y,
			self.zoom_level, self.tile_x, self.tile_y, stop_level,
			config, count, log_file, start_checks_zoom, check_full)

def quad_tree_gen_node_from_json(json_str):
	node = QuadTreeGenNode()
	node.from_json(json_str)
	return node

class TileNotFoundException(Exception):
	def __init__(self, *args):
		self.value = args

	def __repr__(self):
		return repr(self.value)

class NullStorageManager:
	def __init__(self):
		pass

	def fetch(self, zoom_level, x, y):
		pass

	def store(self, node, img_bytes):
		pass

	def __del__(self):
		self.close()

	def flush(self):
		pass

	def close(self):
		pass

class NullRenderer:
	def __init__(self, img_w=256, img_h=256, img_prefix='images/', info_cache_name=None):
		self.img_w = img_w
		self.img_h = img_h
		self.blank_img_id = -1
		self.blank_img_bytes = None 
		self.full_img_id = -2
		self.full_img_bytes = None 
		self.info_cache_name = info_cache_name
		self.info_cache = None

	def set_info_cache(self, cache):
		self.info_cache = cache

	def cache_tile_info(self, node):
		if(self.info_cache != None):
			self.info_cache.add_node_info(node.node_id, {
				'is_full': node.is_full,
				'is_blank': node.is_blank,
				'is_leaf': node.is_leaf,
				})

	def render_full(self):
		if(self.full_img_bytes == None):
			palette = ImagePalette.ImagePalette("RGB").palette
			image = Image.new("P",(self.img_w,self.img_h),0)
			image.putpalette(palette)
			self.full_img_bytes = StringIO.StringIO()
			image.save(self.full_img_bytes, 'png')

		return (self.full_img_id, self.full_img_bytes)

	def render_blank(self):
		if(self.blank_img_bytes == None):
			palette = ImagePalette.ImagePalette("RGB").palette
			image = Image.new("P",(self.img_w,self.img_h),0)
			image.putpalette(palette)
			self.blank_img_bytes = StringIO.StringIO()
			image.save(self.blank_img_bytes, 'png')

		return (self.blank_img_id, self.blank_img_bytes)

	#updates node with relevant info
	def tile_info(self, node, check_full=True):
		return None

	def render_normal(self, node):
		return self.render_blank()

	def render(self, node):
		return (0, StringIO.StringIO('') )

class Renderer(NullRenderer):
	def __init__(self, img_w=256, img_h=256, info_cache_name=None):
		NullRenderer.__init__(self, img_w, img_h, info_cache_name=info_cache_name)

	def tile_info(self, node, check_full=True):
		node.is_blank = False
		node.is_full = False
		node.is_leaf = False

		if(node.geom == None or (hasattr(node.geom, 'is_empty') and node.geom.is_empty)):
			node.is_blank = True
			node.is_leaf = True
		elif(check_full):
			bbox = shapely.wkt.loads("POLYGON((%(min_x)s %(min_y)s, %(min_x)s %(max_y)s, %(max_x)s  %(max_y)s, %(max_x)s %(min_y)s, %(min_x)s %(min_y)s))" % 
				{'min_x': node.min_x, 'min_y': node.min_y, 'max_x': node.max_x, 'max_y': node.max_y})
			if(type(node.geom) == list):
				for geom in node.geom:
					if(geom.contains(bbox)):
						node.is_full = True
						node.is_leaf = True
						break
			else:
				if(node.geom.contains(bbox)):
					node.is_full = True
					node.is_leaf = True

	def render(self, node):
		if(node.is_blank):
			return self.render_blank()
		elif(node.is_full):
			return self.render_full()
		return self.render_normal(node)

class QuadTreeGenStats:
	def __init__(self, start_zoom, stop_zoom, savings_guess=ESTIMATED_SAVINGS):
		self.nodes_rendered = [0]*(stop_zoom+1)
		self.blanks_rendered = [0]*(stop_zoom+1)
		self.fulls_rendered = [0]*(stop_zoom+1)
		self.leafs_rendered = [0]*(stop_zoom+1)
		self.total_nodes_rendered = 0
		self.total_blanks_rendered = 0
		self.total_fulls_rendered = 0
		self.total_leafs_rendered = 0
		self.start_time = time.time()
		self.stop_time = self.start_time
		self.start_zoom = start_zoom
		self.stop_zoom = stop_zoom
		self.virtual_nodes = 0
		self.virtual_percent_complete = 0
		self.virtual_total_nodes = float((4*(4**(stop_zoom - start_zoom)) -1)/3.0)
		self.savings_guess = savings_guess

	def stop_timer(self):
		self.stop_time = time.time()
	
	def reset_timer(self):
		self.start_time = time.time()
		self.stop_time = None

	def track(self, node, is_leaf=False):
		if(node.is_blank):
			self.blanks_rendered[node.zoom_level] += 1
			self.total_blanks_rendered += 1
		elif(node.is_full):
			self.fulls_rendered[node.zoom_level] += 1
			self.total_fulls_rendered += 1
		if(node.is_leaf or is_leaf):
			self.leafs_rendered[node.zoom_level] += 1
			self.total_leafs_rendered += 1
		self.nodes_rendered[node.zoom_level] += 1
		self.total_nodes_rendered += 1

		#if this is a leaf node calculate how much of the tree has been completed
		#A leaf node means that itself, and its entire sub tree have been completed
		if(node.is_leaf):
			#the number of nodes in this node's subtree (including itself)
			num_finished = (4*(4**(self.stop_zoom - node.zoom_level)) -1)/3.0
			self.virtual_nodes += num_finished
		else:
			self.virtual_nodes += 1

		self.virtual_percent_complete = self.virtual_nodes / self.virtual_total_nodes

	def __repr__(self):
		return 'time: %f, est: %f, vprogress:%f, nps: %f, nodes: %d, blanks: %d, fulls: %d, savings: %f' %\
			(self.time(), self.time_est(), self.virtual_percent_complete,
				self.nodes_per_sec(),
				self.total_nodes_rendered, self.total_blanks_rendered, self.total_fulls_rendered, self.savings())

	def get_nodes_rendered(self):
		return self.nodes_rendered

	def savings(self):
		if(self.virtual_nodes > 0):
			return 1 - (self.total_nodes_rendered / float(self.virtual_nodes))
		return float('nan')

	def time(self):
		if(self.stop_time != None):
			return (self.stop_time - self.start_time) 
		return (time.time() - self.start_time) 

	def time_est(self):
		#calculate the expected number of nodes that will be rendered based on what we have
		#rendered so far
		est_node_count = 0
		cumulative_prob = 0
		for z in range(self.stop_zoom + 1):
			this_prob = 0
			if(self.nodes_rendered[z] != 0):
				this_prob = (1 - cumulative_prob) * (self.leafs_rendered[z] /float(self.nodes_rendered[z]))
			est_node_count += (4**z) * (this_prob)
			cumulative_prob += this_prob

		#take our a priori knowlege into account
		final_est_node_count = (self.virtual_percent_complete) * est_node_count + \
				(1 - self.virtual_percent_complete) * ((1-self.savings_guess) * self.virtual_total_nodes)

		nps = self.nodes_per_sec()
		if(nps > 0):
			return final_est_node_count / nps - self.time()
		return float('nan')

	def nodes_per_sec(self):
		time = self.time()
		if(time > 0):
			return self.total_nodes_rendered / time
		return float('nan')

def load_cutter(config):
	cutter_type = config.get('cutter_type', 'multi')
	if(cutter_type == 'shapefileram'):
		return load_shapefile_ram_cutter(config['shapefile_path'], config['shapefile_layer'])
	if(cutter_type == 'shapefile'):
		return load_shapefile_cutter(config['shapefile_path'], config['shapefile_layer'])
	elif(cutter_type == 'maptree'):
		return load_maptree_cutter(config['shapefile_path'], config['shapefile_layer'])
	elif(cutter_type == 'postgres'):
		return load_postgres_cutter(config['connect_string'], config['table_name'])
	elif(cutter_type == 'multi'):
		cutters = []
		for layer_name in config['layer_order']:
			layer_config = config['layers'][layer_name]
			cutters.append(load_cutter(layer_config))
		return multi.MultiCutter(cutters)
	else:
		return NullGeomCutter()

def load_label_classes(layer_config, label_renderer):
	for layer_name, label_classes in layer_config['label_classes'].items():
		for label_class_dict in label_classes:
			label_class = label.LabelClass()
			label_class.from_dict(label_class_dict)
			label_renderer.add_label_class(layer_name, label_class)

def load_storage_manager(config, job_id, run_prefix=''):
	storage_type = config.get('dist_render_storage_type', 'multi')
	if(storage_type == 'csv'):
		prefix = config['output_prefix'] + run_prefix
		tree_file_path =  prefix + 'tree_%d.csv' % job_id
		image_file_path = prefix + 'images_%d.csv' % job_id
		return csvstorage.CSVStorageManager(open(tree_file_path, 'w'), open(image_file_path, 'w'))
	elif(storage_type == 'multi'):
		storage_managers = []
		for layer_name in config['layer_order']:
			layer_config = config['layers'][layer_name]
			storage_managers.append(load_storage_manager(layer_config, job_id, run_prefix))
		return multi.MultiStorageManager(storage_managers)

def load_renderer(config):
	renderer_type = config.get('renderer_type', 'multi')

	if(renderer_type == 'mapserver'):
		mapfile_path = config['mapfile_path']
		if(isinstance(mapfile_path, list)):
			mapfile_path = mapfile_path[0]
		return mapserver.MapServerRenderer(open(mapfile_path,'r').read(),
			config['mapserver_layers'], img_w=256, img_h=256, img_buffer=config.get('img_buffer', 0),
			min_zoom=config.get('min_zoom', 0), max_zoom=config.get('max_zoom', 20),
			cache_fulls=config.get('cache_fulls', True), srs=config.get('srs', 'EPSG:3857'),
			trust_cutter=config.get('trust_cutter', False), tile_buffer=config.get('tile_buffer', 0),
			info_cache_name=config.get('tile_info_cache', None),
			skip_info=config.get('skip_info',False))

	elif(renderer_type == 'label'):
		mapfile_path = config['mapfile_path']
		if(isinstance(mapfile_path, list)):
			mapfile_path = mapfile_path[0]
		renderer = label.LabelRenderer(open(mapfile_path,'r').read(),
			config.get('label_col_index', None), config['mapserver_layers'],
			config.get('min_zoom', 0), config.get('max_zoom', 100),
			point_labels=config.get('point_labels', False))
		load_label_classes(config, renderer)
		return renderer

	elif(renderer_type == 'multi'):
		renderers = []
		for layer_name in config['layer_order']:
			layer_config = config['layers'][layer_name]
			renderers.append(load_renderer(layer_config))
		return multi.MultiRenderer(renderers)

	return None

def load_postgres_cutter(connect_str, table_name):
	return postgres.PostgresCutter(connect_str, table_name)

def load_shapefile_cutter(shapefile_path, shapefile_layer):
	if(isinstance(shapefile_path, list)):
		shapefile_path = shapefile_path[0]
	return  shapefile.ShapefileCutter(shapefile_path, str(shapefile_layer))

def load_shapefile_ram_cutter(shapefile_path, shapefile_layer):
	if(isinstance(shapefile_path, list)):
		shapefile_path = shapefile_path[0]
	return  shapefile.ShapefileRAMCutter(shapefile_path, str(shapefile_layer))

def load_maptree_cutter(shapefile_path, shapefile_layer):
	shapefile_root = os.path.basename(shapefile_path)
	qix_path = shapefile_root + '.qix'
	return shapefile.MaptreeCutter(shapefile_path, str(shapefile_layer), qix_path)

class GeneratorJob:
	def __init__(self, min_x, min_y, max_x, max_y, start_level,
			start_tile_x, start_tile_y, stop_level, config, count=0,
			log_file=sys.stdout, start_checks_zoom=None,
			check_full=True):
		self.min_x = min_x
		self.min_y = min_y
		self.max_x = max_x
		self.max_y = max_y
		self.start_level = start_level
		self.start_tile_x = start_tile_x
		self.start_tile_y = start_tile_y
		self.stop_level = stop_level
		self.config = config
		self.count = count
		self.log_file = log_file
		self.start_checks_zoom = start_checks_zoom
		self.check_full = check_full

	def load_cutter(self):
		return load_cutter(self.config)

	def load_renderer(self):
		return load_renderer(self.config)

	def load_storage_manager(self):
		return load_storage_manager(self.config, self.count, self.config.get('run_prefix', ''))

def generate_node(node, cutter, storage_manager, renderer, stop_level, stats, start_checks_zoom=None, check_full=True):
	if(start_checks_zoom == None or node.zoom_level >= start_checks_zoom):
		#is this node a leaf?
		renderer.tile_info(node, check_full)

	#render this node
	node.image_id, this_img_bytes = renderer.render(node)

	if(node.zoom_level >= stop_level):
		stats.track(node, True)
	else:
		stats.track(node, False)
	
	storage_manager.store(node, this_img_bytes)

	#split this node 
	if(node.is_leaf or node.zoom_level >= stop_level):
		return []

	#figure out the geometry associated with a node at start_checks_zoom - 1
	#so that the next tile_info() call won't find a None value for geometry
	if(start_checks_zoom == None or node.zoom_level >= (start_checks_zoom - 1)):
		return node.split(cutter)
	return node.split()

#def generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, start_level=0, start_tile_x=0, start_tile_y=0, stop_level=17, log_file=sys.stdout, start_checks_zoom=0, check_full=True):

def generate(job):
	storage_manager = job.load_storage_manager()
	renderer = job.load_renderer()
	cutter = job.load_cutter()
	log_file = job.log_file

	stats = QuadTreeGenStats(job.start_level, job.stop_level)
	stats.reset_timer()

	#create the initial QuadTreeGenNode
	root_node = QuadTreeGenNode(None,job.min_x,job.min_y,job.max_x,job.max_y,
		zoom_level=job.start_level, tile_x=job.start_tile_x, tile_y=job.start_tile_y)
	root_geom = None
	if(job.start_checks_zoom == None or root_node.zoom_level >= job.start_checks_zoom):
		root_node.geom = cutter.cut(job.min_x, job.min_y, job.max_x, job.max_y)

	nodes_to_render = [root_node]
	last_stat_output = time.time()

	while(len(nodes_to_render) > 0):
		this_node = nodes_to_render.pop()
		children = generate_node(this_node, cutter, storage_manager, renderer, job.stop_level, stats,
				job.start_checks_zoom, job.check_full)
		nodes_to_render.extend(children)

		#output stats every so often
		now = time.time()
		if(now - last_stat_output > 5):
			log_file.write(str(stats))
			log_file.write('\n')
			log_file.flush()
			last_stat_output = now

	storage_manager.flush()
	stats.stop_timer()
	log_file.write(str(stats))
	log_file.write('\n')
	log_file.flush()

def generate_mt(generator_jobs, num_threads=multiprocessing.cpu_count()):
	#line up
	threads = []
	num_threads = min(num_threads, len(generator_jobs))
	for x in range(num_threads):
		thread = multiprocessing.Process(target=generate, args=[generator_jobs.pop()])
		threads.append(thread)

	#off to the races
	for thread in threads:
		thread.start()

	#check every 10 seconds to see if a thread has finished 
	while(len(generator_jobs) > 0):
		for x in range(len(threads)):
			if(not threads[x].is_alive()):
				del threads[x]
				new_thread = multiprocessing.Process(target=generate, args=[generator_jobs.pop()])
				threads.append(new_thread)
				new_thread.start()
				break

		time.sleep(10)

	#wait for everyone to finish
	for thread in threads:
		thread.join()

def cmp_nodes(node1, node2):
	if(node1.tile_x == node2.tile_x):
		return node1.tile_y < node2.tile_y
	return node1.tile_x < node2.tile_x

def encode_img_bytes(img_bytes):
	return img_bytes.encode('string_escape')

def decode_img_bytes(img_bytes):
	return img_bytes.decode('string_escape')

