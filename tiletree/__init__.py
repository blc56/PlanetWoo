##\file __init__.py Main classes for the tiletree module. 
import Image
import ImagePalette
import ImageDraw
import StringIO
import os
import mapscript

##\brief A simple, QuadTreeNode
#
class QuadTreeGenNode:
	##\param node_id - integer
	#
	def __init__(self, node_id=0, min_x=0, min_y=0, max_x=0, max_y=0, zoom_level=0,
			image_id=None, is_leaf=True, is_blank=True, is_full=False,
			child_0=None, child_1=None, child_2=None, child_3=None,
			parent_geom=None, tile_x=0, tile_y=0):
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
		self.parent_geom = parent_geom
		self.tile_x = tile_x
		self.tile_y = tile_y

	def to_csv(self):
		return ','.join(repr(x) for x in [self.node_id, self.zoom_level, self.min_x, self.min_y,
			self.max_x, self.max_y, self.image_id, self.is_leaf, self.is_blank, self.is_full,
			self.child_0, self.child_1, self.child_2, self.child_3, self.tile_x, self.tile_y])

	def __repr__(self):
		return repr(self.__dict__)

class CSVStorageManager:
	def __init__(self, tree_file, image_file, image_prefix='images/', image_suffix='.png'):
		self.tree_file = tree_file
		self.image_file = image_file
		self.image_prefix = image_prefix
		self.image_suffix = image_suffix

		self.tree_file.write(','.join(['node_id', 'zoom_level', 'min_x', 'min_y', 'max_x', 'max_y',
			'image_id', 'is_leaf', 'is_blank', 'is_full',
			'child_0', 'child_1', 'child_2', 'child_3', 'tile_x', 'tile_y']))
		self.tree_file.write('\n')

		self.image_file.write(','.join(['image_id', 'image_fn']))
		self.image_file.write('\n')

	def lookup_tile(self, zoom_level, x, y):
		raise Exception("Not implemented")

	def _get_storage_path(self, node):
		return self.image_prefix + repr(node.image_id) + self.image_suffix

	def store(self, node, img_bytes):
		self.tree_file.write(node.to_csv())
		self.tree_file.write('\n')

		img_fn = self._get_storage_path(node)
		if(not os.path.exists(img_fn)):
			#create the image
			open(img_fn, 'w').write(img_bytes.getvalue())
			#also output the information to the csv
			self.image_file.write(','.join([repr(node.node_id), img_fn]))
			self.image_file.write('\n')

	def close(self):
		self.tree_file.close()
		self.image_file.close()

class FSStorageManager:
	def __init__(self, image_prefix='images/', image_suffix='.png'):
		self.image_prefix = image_prefix
		self.image_suffix = image_suffix

	def get_slippy_path(self, zoom_level, x, y):
		#store in OSM slippy tile structure
		link_dir = os.path.join(self.image_prefix, str(zoom_level), str(x))
		link_fn = os.path.join(link_dir, str(y)) + self.image_suffix

		return (link_dir, link_fn)

	def _get_storage_path(self, node):
		return self.image_prefix + repr(node.image_id) + self.image_suffix

	def fetch(self, zoom_level, x, y):
		path = self.get_slippy_path(zoom_level, x, y)[1]
		return open(path, 'r')

	def store(self, node, img_bytes):
		img_fn = self._get_storage_path(node)
		if(not os.path.exists(img_fn)):
			#create the image
			open(img_fn, 'w').write(img_bytes.getvalue())

		#now create a sym link to the image (slippymap style)
		link_dir, link_fn = self.get_slippy_path(node.zoom_level, node.tile_x, node.tile_y)
		if(not os.path.isdir(link_dir)):
			os.makedirs(link_dir)
		os.symlink(os.path.abspath(img_fn), link_fn)

	def close(self):
		pass

class GeomCutter:
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
		return (True, False, False)

	def render_normal(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		return self.render_blank()

	def render(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		if(is_blank):
			return self.render_blank()
		elif(is_full):
			return self.render_full()
		return self.render_normal(geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level)

class MapServerRenderer(NullRenderer):
	def __init__(self, mapfile_template, layers, img_w=256, img_h=256, img_prefix='images/'):
		NullRenderer.__init__(self, img_w, img_h, img_prefix)
		self.mapfile_template=mapfile_template
		self.layers=layers

	def tile_info(self, geometry, min_x, min_y, max_x, max_y, zoom_level):
		#TODO: FIXME
		return (False, False, False)

	def render_normal(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		wms_req = mapscript.OWSRequest()

		#TODO:BLC: XXX replace this with geometry!!!
		template_args = {
			'wkt': "POLYGON((5 5, 5 10, 10 10, 10 5, 5 5))",
		}
		mapfile = mapscript.fromstring(self.mapfile_template % template_args)

		wms_req.setParameter('MODE', 'WMS')
		wms_req.setParameter('VERSION', '1.1.1')
		wms_req.setParameter('FORMAT', 'image/png')
		wms_req.setParameter('TRANSPARENT', 'TRUE')
		wms_req.setParameter('WIDTH', str(self.img_w))
		wms_req.setParameter('HEIGHT', str(self.img_h))
		wms_req.setParameter('SRS', 'EPSG:3857')
		wms_req.setParameter('REQUEST', 'GetMap')
		wms_req.setParameter('BBOX', ','.join(str(x) for x in [min_x, min_y, max_x, max_y]))
		wms_req.setParameter('LAYERS', self.layers)

		mapscript.msIO_installStdoutToBuffer()
		mapfile.OWSDispatch(wms_req)
		mapscript.msIO_stripStdoutBufferContentType()

		img_id = self.next_img_id
		self.next_img_id += 1

		return (img_id, StringIO.StringIO(mapscript.msIO_getStdoutBufferBytes()))

##\brief A simple, QuadTree structure
#
class QuadTreeGenerator:
	def __init__(self):
		self.next_node_id = 0

	def generate_node(self, node, geom, storage_manager, renderer, num_levels):

		#is this node a leaf?
		node.is_blank, node.is_full, node.is_leaf =\
			renderer.tile_info(geom, node.min_x, node.min_y, node.max_x, node.max_y, node.zoom_level)

		if(node.zoom_level >= num_levels):
			node.is_leaf = True

		#render this node
		node.image_id, this_img_bytes =\
			renderer.render(geom, node.is_blank, node.is_full, node.is_leaf,
				node.min_x, node.min_y, node.max_x, node.max_y, node.zoom_level)
		
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

		min_x1 = max_x0
		min_y1 = node.min_y
		max_x1 = node.max_x
		max_y1 = max_y0
		tile_x1 = node.tile_x * 2 + 1
		tile_y1 = node.tile_y * 2

		min_x2 = node.min_x
		min_y2 = max_y0
		max_x2 = max_x0
		max_y2 = node.max_y
		tile_x2 = node.tile_x * 2
		tile_y2 = node.tile_y * 2 + 1

		min_x3 = max_x0
		min_y3 = max_y0
		max_x3 = node.max_x
		max_y3 = node.max_y
		tile_x3 = node.tile_x * 2 + 1
		tile_y3 = node.tile_y * 2 + 1

		child0 = QuadTreeGenNode(self.next_node_id, min_x0, min_y0, max_x0, max_y0, this_zoom,
				parent_geom=geom, tile_x=tile_x0, tile_y=tile_y0)
		self.next_node_id += 1

		child1 = QuadTreeGenNode(self.next_node_id, min_x1, min_y1, max_x1, max_y1, this_zoom,
				parent_geom=geom, tile_x=tile_x1, tile_y=tile_y1)
		self.next_node_id += 1

		child2 = QuadTreeGenNode(self.next_node_id, min_x2, min_y2, max_x2, max_y2, this_zoom,
				parent_geom=geom, tile_x=tile_x2, tile_y=tile_y2)
		self.next_node_id += 1

		child3 = QuadTreeGenNode(self.next_node_id, min_x3, min_y3, max_x3, max_y3, this_zoom,
				parent_geom=geom, tile_x=tile_x3, tile_y=tile_y3)
		self.next_node_id += 1

		return (child0, child1, child2, child3)

	def generate(self, min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, num_levels=17):
		self.next_node_id = 0

		#create the initial QuadTreeGenNode
		root_node = QuadTreeGenNode(self.next_node_id,min_x,min_y,max_x,max_y,0)
		self.next_node_id += 1

		nodes_to_render = [root_node]

		while(len(nodes_to_render) > 0):
			this_node = nodes_to_render.pop(0)
			this_geom = cutter.cut(this_node.min_x, this_node.min_y, this_node.max_x, this_node.max_y, this_node.parent_geom)
			children = self.generate_node(this_node, this_geom, storage_manager, renderer, num_levels)
			nodes_to_render.extend(children)

