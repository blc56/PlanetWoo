##\file __init__.py Main classes for the tiletree module. 
import Image
import ImagePalette
import ImageDraw
import StringIO
import mapscript
import copy
import shapely
import shapely.wkt
import json
import time
import shapely.speedups

#if(shapely.speedups.available):
	#shapely.speedups.enable()
	#print "SPEEDUP?"

##\brief A simple, QuadTreeNode
#
class QuadTreeGenNode:
	##\param node_id - integer
	#
	def __init__(self, node_id=0, min_x=0, min_y=0, max_x=0, max_y=0, zoom_level=0,
			image_id=None, is_leaf=True, is_blank=True, is_full=False,
			child_0=None, child_1=None, child_2=None, child_3=None,
			geom=None,tile_x=0, tile_y=0):
		self.node_id = node_id
		self.min_x = min_x
		self.min_y = min_y
		self.max_x = max_x
		self.max_y = max_y
		self.zoom_level = zoom_level
		self.image_id = image_id
		self.is_leaf = is_leaf
		self.is_blank = is_blank
		self.is_full = is_full
		self.child_0 = child_0
		self.child_1 = child_1
		self.child_2 = child_2
		self.child_3 = child_3
		self.geom = geom
		self.tile_x = tile_x
		self.tile_y = tile_y

	def __repr__(self):
		return repr(self.__dict__)

	def to_dict(self):
		return copy.copy(self.__dict__)

	def to_json(self):
		self_dict = self.to_dict()
		if(self.geom):
			self_dict['geom'] = shapely.wkt.dumps(self.geom)
		return json.dumps(self_dict)

	def from_json(self, json_str):
		self.__dict__.update(json.loads(json_str))
		if(self.geom):
			self.geom = shapely.wkt.loads(self.geom)

def quad_tree_gen_node_from_json(json_str):
	node = QuadTreeGenNode()
	node.from_json(json_str)
	return node

class NullStorageManager:
	def __init__(self):
		pass

	def fetch(self, zoom_level, x, y):
		pass

	def store(self, node, img_bytes):
		pass

	def close(self):
		pass

class NullGeomCutter:
	def __init__(self):
		pass

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		#raise Exception("Not implemented")
		#return None
		return 0

class NullRenderer:
	def __init__(self, img_w=256, img_h=256, img_prefix='images/'):
		self.img_w = img_w
		self.img_h = img_h
		self.blank_img_id = None
		self.blank_img_bytes = None 
		self.full_img_id = None
		self.full_img_bytes = None 
		self.next_img_id = 0

	def render_full(self):
		if(self.full_img_id == None):
			self.full_img_id = self.next_img_id

			palette = ImagePalette.ImagePalette("RGB").palette
			image = Image.new("P",(self.img_w,self.img_h),0)
			image.putpalette(palette)
			self.full_img_bytes = StringIO.StringIO()
			image.save(self.full_img_bytes, 'png')

			self.next_img_id += 1

		return (self.full_img_id, self.full_img_bytes)

	def render_blank(self):
		if(self.blank_img_id == None):
			self.blank_img_id = self.next_img_id

			palette = ImagePalette.ImagePalette("RGB").palette
			image = Image.new("P",(self.img_w,self.img_h),0)
			image.putpalette(palette)
			self.blank_img_bytes = StringIO.StringIO()
			image.save(self.blank_img_bytes, 'png')

			self.next_img_id += 1

		return (self.blank_img_id, self.blank_img_bytes)

	#\return (is_blank, is_full, is_leaf)
	def tile_info(self, geometry, min_x, min_y, max_x, max_y, zoom_level):
		is_blank = False
		is_full = False
		is_leaf = False

		if(geometry == None or geometry.is_empty):
			is_blank = True
			is_leaf = True
		else:
			bbox = shapely.wkt.loads("POLYGON((%(min_x)s %(min_y)s, %(min_x)s %(max_y)s, %(max_x)s  %(max_y)s, %(max_x)s %(min_y)s, %(min_x)s %(min_y)s))" % 
				{'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y})
			if(geometry.contains(bbox)):
				is_full = True
				is_leaf = True

		return (is_blank, is_full, is_leaf)

	def render_normal(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		return self.render_blank()

	def render(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		return (0, StringIO.StringIO('') )
		#if(is_blank):
			#return self.render_blank()
		#elif(is_full):
			#return self.render_full()
		#return self.render_normal(geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level)

class QuadTreeGenStats:
	def __init__(self):
		self.nodes_rendered = 0
		self.blanks_rendered = 0
		self.fulls_rendered = 0
		self.start_time = time.time()
		self.stop_time = self.start_time

	def stop_timer(self):
		self.stop_time = time.time()
	
	def reset_timer(self):
		self.start_time = time.time()
		self.stop_time = None

	def track(self, is_blank, is_full):
		if(is_blank):
			self.blanks_rendered += 1
		elif(is_full):
			self.fulls_rendered += 1
		self.nodes_rendered += 1

	def __repr__(self):
		if(self.stop_time != None):
			return 'time: %f, nps: %f, cnps: %f, nodes: %d, blanks: %d, fulls: %d' %\
				(self.stop_time - self.start_time, self.nodes_per_sec(), self.content_nodes_per_sec(),
					self.nodes_rendered, self.blanks_rendered, self.fulls_rendered)
		else:
			return 'time: %f, nps: %f, cnps: %f, nodes: %d, blanks: %d, fulls: %d' %\
				(time.time() - self.start_time, self.nodes_per_sec(), self.content_nodes_per_sec(),
					self.nodes_rendered, self.blanks_rendered, self.fulls_rendered)

	def get_nodes_rendered(self):
		return self.nodes_rendered

	def content_nodes_per_sec(self):
		if(self.stop_time != None and (self.stop_time - self.start_time) != 0):
			return (self.nodes_rendered - (self.blanks_rendered + self.fulls_rendered)) /\
				(self.stop_time - self.start_time) 
		if(self.stop_time == None and (time.time() - self.start_time != 0)):
			return (self.nodes_rendered - (self.blanks_rendered + self.fulls_rendered)) /\
				(time.time() - self.start_time) 
		return float('nan')

	def nodes_per_sec(self):
		if(self.stop_time != None and (self.stop_time - self.start_time) != 0):
			return self.nodes_rendered / (self.stop_time - self.start_time) 
		if(self.stop_time == None and (time.time() - self.start_time != 0)):
			return self.nodes_rendered / (time.time() - self.start_time) 
		return float('nan')

##\brief A simple, QuadTree structure
#
class QuadTreeGenerator:
	def __init__(self):
		self.next_node_id = 0

	def generate_node(self, node, cutter, storage_manager, renderer, num_levels, stats):

		#is this node a leaf?
		node.is_blank, node.is_full, node.is_leaf =\
			renderer.tile_info(node.geom, node.min_x, node.min_y, node.max_x, node.max_y, node.zoom_level)

		if(node.zoom_level >= num_levels):
			node.is_leaf = True

		#render this node
		node.image_id, this_img_bytes =\
			renderer.render(node.geom, node.is_blank, node.is_full, node.is_leaf,
				node.min_x, node.min_y, node.max_x, node.max_y, node.zoom_level)

		stats.track(node.is_blank, node.is_full)
		
		#store this node
		if(not node.is_leaf):
			node.child_0 = self.next_node_id
			node.child_1 = self.next_node_id + 1
			node.child_2 = self.next_node_id + 2
			node.child_3 = self.next_node_id + 3
		storage_manager.store(node, this_img_bytes)

		#split this node 
		if(node.is_leaf):
			return []

		#calculate new coordinates for child nodes
		#assume mercator when create tile coordinates
		#I guess I hate mapping
		this_zoom = node.zoom_level + 1
		min_x0 = node.min_x
		min_y0 = node.min_y
		max_x0 = node.min_x + (node.max_x - node.min_x) / 2.0
		max_y0 = node.min_y + (node.max_y - node.min_y) / 2.0
		tile_x0 = node.tile_x * 2
		tile_y0 = node.tile_y * 2
		geom0 = cutter.cut(min_x0, min_y0, max_x0, max_y0, node.geom)

		min_x1 = max_x0
		min_y1 = node.min_y
		max_x1 = node.max_x
		max_y1 = max_y0
		tile_x1 = node.tile_x * 2 + 1
		tile_y1 = node.tile_y * 2
		geom1 = cutter.cut(min_x1, min_y1, max_x1, max_y1, node.geom)

		min_x2 = node.min_x
		min_y2 = max_y0
		max_x2 = max_x0
		max_y2 = node.max_y
		tile_x2 = node.tile_x * 2
		tile_y2 = node.tile_y * 2 + 1
		geom2 = cutter.cut(min_x2, min_y2, max_x2, max_y2, node.geom)

		min_x3 = max_x0
		min_y3 = max_y0
		max_x3 = node.max_x
		max_y3 = node.max_y
		tile_x3 = node.tile_x * 2 + 1
		tile_y3 = node.tile_y * 2 + 1
		geom3 = cutter.cut(min_x3, min_y3, max_x3, max_y3, node.geom)

		#do the tile coordinates slippy map style instead of TMS style
		child0 = QuadTreeGenNode(self.next_node_id, min_x0, min_y0, max_x0, max_y0, this_zoom,
				geom=geom0, tile_x=tile_x0, tile_y=tile_y2)
		self.next_node_id += 1

		child1 = QuadTreeGenNode(self.next_node_id, min_x1, min_y1, max_x1, max_y1, this_zoom,
				geom=geom1, tile_x=tile_x1, tile_y=tile_y3)
		self.next_node_id += 1

		child2 = QuadTreeGenNode(self.next_node_id, min_x2, min_y2, max_x2, max_y2, this_zoom,
				geom=geom2, tile_x=tile_x2, tile_y=tile_y0)
		self.next_node_id += 1

		child3 = QuadTreeGenNode(self.next_node_id, min_x3, min_y3, max_x3, max_y3, this_zoom,
				geom=geom3, tile_x=tile_x3, tile_y=tile_y1)
		self.next_node_id += 1

		return (child0, child1, child2, child3)

	def generate(self, min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=17):
		stats = QuadTreeGenStats()
		stats.reset_timer()
		self.next_node_id = 0

		#create the initial QuadTreeGenNode
		root_node = QuadTreeGenNode(self.next_node_id,min_x,min_y,max_x,max_y,0)
		root_geom = cutter.cut(min_x, min_y, max_x, max_y)
		root_node.geom = root_geom
		self.next_node_id += 1

		nodes_to_render = [root_node]

		while(len(nodes_to_render) > 0):
			this_node = nodes_to_render.pop()
			#print this_node.zoom_level, this_node.tile_x, this_node.tile_y, len(nodes_to_render)
			children = self.generate_node(this_node, cutter, storage_manager, renderer, num_levels, stats)
			nodes_to_render.extend(children)

			if(stats.get_nodes_rendered() % 100 == 0):
				print stats

		stats.stop_timer()
		print stats

