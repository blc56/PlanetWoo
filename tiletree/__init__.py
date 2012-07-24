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

#if(shapely.speedups.available):
	#shapely.speedups.enable()
	#print "SPEEDUP?"

def bbox_to_wkt(min_x, min_y, max_x, max_y):
	return "POLYGON((%(min_x)s %(min_y)s, %(max_x)s %(min_y)s, %(max_x)s %(max_y)s, %(min_x)s %(max_y)s, %(min_x)s %(min_y)s))" % {
		'min_x': min_x,
		'min_y': min_y,
		'max_x': max_x,
		'max_y': max_y,
	}

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
			#child_0=None, child_1=None, child_2=None, child_3=None,
			geom=None,tile_x=0, tile_y=0):
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
		#self.child_0 = child_0
		#self.child_1 = child_1
		#self.child_2 = child_2
		#self.child_3 = child_3
		self.geom = geom
		self.tile_x = tile_x
		self.tile_y = tile_y

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
				is_leaf=self.is_leaf, is_blank=self.is_blank, is_full=self.is_full)

		child1 = QuadTreeGenNode(None, min_x1, min_y1, max_x1, max_y1, this_zoom,
				image_id=image_id, geom=geom1, tile_x=tile_x1, tile_y=tile_y3,
				is_leaf=self.is_leaf, is_blank=self.is_blank, is_full=self.is_full)

		child2 = QuadTreeGenNode(None, min_x2, min_y2, max_x2, max_y2, this_zoom,
				image_id=image_id, geom=geom2, tile_x=tile_x2, tile_y=tile_y0,
				is_leaf=self.is_leaf, is_blank=self.is_blank, is_full=self.is_full)

		child3 = QuadTreeGenNode(None, min_x3, min_y3, max_x3, max_y3, this_zoom,
				image_id=image_id, geom=geom3, tile_x=tile_x3, tile_y=tile_y1,
				is_leaf=self.is_leaf, is_blank=self.is_blank, is_full=self.is_full)

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

	def to_generator_job(self, storage_manager, renderer, cutter, stop_level, log_file=sys.stdout, start_checks_zoom=None, check_full=True):
		return GeneratorJob(self.min_x, self.min_y, self.max_x, self.max_y,
			self.zoom_level, self.tile_x, self.tile_y, stop_level,
			storage_manager, renderer, cutter, log_file, start_checks_zoom, check_full)

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
	def __init__(self, img_w=256, img_h=256, img_prefix='images/'):
		self.img_w = img_w
		self.img_h = img_h
		self.blank_img_id = -1
		self.blank_img_bytes = None 
		self.full_img_id = -2
		self.full_img_bytes = None 

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

	#\return (is_blank, is_full, is_leaf)
	def tile_info(self, node, check_full=True):
		is_blank = False
		is_full = False
		is_leaf = False
		return (is_blank, is_full, is_leaf)

	def render_normal(self, node):
		return self.render_blank()

	def render(self, node):
		return (0, StringIO.StringIO('') )

class Renderer(NullRenderer):
	def __init__(self, img_w=256, img_h=256):
		NullRenderer.__init__(self, img_w, img_h)

	#\return (is_blank, is_full, is_leaf)
	def tile_info(self, node, check_full=True):
		is_blank = False
		is_full = False
		is_leaf = False

		if(node.geom == None or (hasattr(node.geom, 'is_empty') and node.geom.is_empty)):
			is_blank = True
			is_leaf = True
		elif(check_full):
			bbox = shapely.wkt.loads("POLYGON((%(min_x)s %(min_y)s, %(min_x)s %(max_y)s, %(max_x)s  %(max_y)s, %(max_x)s %(min_y)s, %(min_x)s %(min_y)s))" % 
				{'min_x': node.min_x, 'min_y': node.min_y, 'max_x': node.max_x, 'max_y': node.max_y})
			if(type(node.geom) == list):
				for geom in node.geom:
					if(geom.contains(bbox)):
						is_full = True
						is_leaf = True
						break
			else:
				if(node.geom.contains(bbox)):
					is_full = True
					is_leaf = True

		return (is_blank, is_full, is_leaf)

	def render(self, node):
		if(node.is_blank):
			return self.render_blank()
		elif(node.is_full):
			return self.render_full()
		return self.render_normal(node)

class QuadTreeGenStats:
	def __init__(self, start_zoom, stop_zoom):
		self.nodes_rendered = 0
		self.blanks_rendered = 0
		self.fulls_rendered = 0
		self.start_time = time.time()
		self.stop_time = self.start_time
		self.start_zoom = start_zoom
		self.stop_zoom = stop_zoom
		self.virtual_nodes = 0
		self.virtual_percent_complete = 0
		self.virtual_total_nodes = float((4*(4**(stop_zoom - start_zoom)) -1)/3.0)

	def stop_timer(self):
		self.stop_time = time.time()
	
	def reset_timer(self):
		self.start_time = time.time()
		self.stop_time = None

	def track(self, node):
		if(node.is_blank):
			self.blanks_rendered += 1
		elif(node.is_full):
			self.fulls_rendered += 1
		self.nodes_rendered += 1

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
		return 'time: %f, est: %f, progress:%f, nps: %f, cnps: %f, nodes: %d, blanks: %d, fulls: %d, savings: %f' %\
			(self.time(), self.time_est(), self.virtual_percent_complete,
				self.nodes_per_sec(), self.content_nodes_per_sec(),
				self.nodes_rendered, self.blanks_rendered, self.fulls_rendered, self.savings())

	def get_nodes_rendered(self):
		return self.nodes_rendered

	def savings(self):
		if(self.virtual_nodes > 0):
			return 1 - (self.nodes_rendered / float(self.virtual_nodes))

	def content_nodes_per_sec(self):
		time = self.time()
		if(time > 0):
			return (self.nodes_rendered - (self.blanks_rendered + self.fulls_rendered)) / time
		return float('nan')

	def time(self):
		if(self.stop_time != None):
			return (self.stop_time - self.start_time) 
		return (time.time() - self.start_time) 

	def time_est(self):
		time = self.time()
		if(time > 0):
			return  (self.virtual_total_nodes - self.virtual_nodes) / (self.virtual_nodes / time)
		return float('nan')

	def nodes_per_sec(self):
		time = self.time()
		if(time > 0):
			return self.nodes_rendered / time
		return float('nan')

class GeneratorJob:
	def __init__(self, min_x, min_y, max_x, max_y, start_level,
			start_tile_x, start_tile_y, stop_level, storage_manager,
			renderer, cutter, log_file=sys.stdout, start_checks_zoom=None,
			check_full=True):
		self.min_x = min_x
		self.min_y = min_y
		self.max_x = max_x
		self.max_y = max_y
		self.start_level = start_level
		self.start_tile_x = start_tile_x
		self.start_tile_y = start_tile_y
		self.stop_level = stop_level
		self.storage_manager = storage_manager
		self.renderer=renderer
		self.cutter = cutter
		self.log_file = log_file
		self.start_checks_zoom = start_checks_zoom
		self.check_full = check_full

def generate_node(node, cutter, storage_manager, renderer, stop_level, stats, start_checks_zoom=None, check_full=True):
	if(start_checks_zoom != None and node.zoom_level >= start_checks_zoom):
		#is this node a leaf?
		node.is_blank, node.is_full, node.is_leaf =\
			renderer.tile_info(node, check_full)

	if(node.zoom_level >= stop_level):
		node.is_leaf = True

	#render this node
	node.image_id, this_img_bytes = renderer.render(node)

	stats.track(node)
	
	storage_manager.store(node, this_img_bytes)

	#split this node 
	if(node.is_leaf):
		return []

	#figure out the geometry associated with a node at start_checks_zoom - 1
	#so that the next tile_info() call won't find a None value for geometry
	if(start_checks_zoom != None and node.zoom_level >= (start_checks_zoom - 1)):
		return node.split(cutter)
	return node.split()

def generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, start_level=0, start_tile_x=0, start_tile_y=0, stop_level=17, log_file=sys.stdout, start_checks_zoom=0, check_full=True):
	stats = QuadTreeGenStats(start_level, stop_level)
	stats.reset_timer()

	#create the initial QuadTreeGenNode
	root_node = QuadTreeGenNode(None,min_x,min_y,max_x,max_y,
		zoom_level=start_level, tile_x=start_tile_x, tile_y=start_tile_y)
	root_geom = None
	if(start_checks_zoom != None and root_node.zoom_level >= start_checks_zoom):
		root_node.geom = cutter.cut(min_x, min_y, max_x, max_y)

	nodes_to_render = [root_node]
	last_stat_output = time.time()

	while(len(nodes_to_render) > 0):
		this_node = nodes_to_render.pop()
		#print this_node.zoom_level, this_node.tile_x, this_node.tile_y, this_node.min_x, this_node.min_y,\
			#this_node.max_x, this_node.max_y
		children = generate_node(this_node, cutter, storage_manager, renderer, stop_level, stats, start_checks_zoom)
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
	#build the arguments that are sent to worker processes
	job_args = []
	for job in generator_jobs:
		job_args.append((job.min_x, job.min_y, job.max_x, job.max_y,
			job.storage_manager, job.renderer, job.cutter,
			job.start_level, job.start_tile_x,
			job.start_tile_y, job.stop_level, job.log_file,
			job.start_checks_zoom,
			job.check_full))
		job.storage_manager.flush()

	#line up
	threads = []
	for x in range(num_threads):
		thread = multiprocessing.Process(target=generate, args=job_args.pop())
		threads.append(thread)

	#off to the races
	for thread in threads:
		thread.start()

	#check every 10 seconds to see if a thread has finished 
	while(len(job_args) > 0):
		for x in range(len(threads)):
			if(not threads[x].is_alive()):
				del threads[x]
				new_thread = multiprocessing.Process(target=generate, args=job_args.pop())
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

