##\file __init__.py Main classes for the tiletree module. 

##\brief A simple, QuadTreeNode
#
class QuadTreeGenNode:
	##\param node_id - integer
	#
	def __init__(self, node_id=0, min_x=0, min_y=0, max_x=0, max_y=0, zoom_level=0,
			image_id=None, is_leaf=True, child_0=None, child_1=None, child_2=None, child_3=None,
			parent_geom=None):
		self.node_id = node_id
		self.min_x = min_x
		self.min_y = min_y
		self.max_x = max_x
		self.max_y = max_y
		self.zoom_level = zoom_level
		self.image_id = image_id
		self.is_leaf = is_leaf
		self.child_0 = child_0
		self.child_1 = child_1
		self.child_2 = child_2
		self.child_3 = child_3
		self.parent_geom = None

	def __repr__(self):
		return repr(self.__dict__)

class CSVStorageManager:
	def __init__(self):
		pass

	def store(self, node, img_fn):
		print node, img_fn

class GeomCutter:
	def __init__(self):
		pass

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		#raise Exception("Not implemented")
		return None

class NullRenderer:
	def __init__(self):
		self.blank_img_id = None
		self.next_img_id = 0
		self.blank_img_fn = None 

	def _render_blank(self):
		if(self.blank_img_id == None):
			self.blank_img_id = self.next_img_id
			self.next_img_id += 1
			self.blank_img_fn = 'blank.png'

		return (self.blank_img_id, self.blank_img_fn)

	def render(self, geometry):
		if(not geometry):
			return self._render_blank()
		raise Exception("Not implemented")

##\brief A simple, QuadTree structure
#
class QuadTreeGenerator:
	def __init__(self):
		self.next_node_id = 0

	def _render_node(self, node, geometry):
		if(geometry):
			raise Exception("Not Implemented")
		else:
			return self.render_blank

	def generate_node(self, node, geom, storage_manager, renderer, num_levels):
		#is this node a leaf?
		if(geom != None and (node.zoom_level + 1) < num_levels ):
			node.is_leaf = False

		#render this node
		node.image_id, this_img_fn = renderer.render(geom)
		
		#store this node
		if(not node.is_leaf):
			node.child_0 = self.next_node_id
			node.child_1 = self.next_node_id + 1
			node.child_2 = self.next_node_id + 2
			node.child_3 = self.next_node_id + 3
		storage_manager.store(node, this_img_fn)

		#split this node 
		if(node.is_leaf):
			return []

		#calculate new coordinates for child nodes
		min_x0 = node.min_x
		min_y0 = node.min_y
		max_x0 = node.max_x / 2.0
		max_y0 = node.max_y / 2.0

		min_x1 = max_x0
		min_y1 = node.min_y
		max_x1 = node.max_x
		max_y1 = max_y0

		min_x2 = node.min_x
		min_y2 = max_y0
		max_x2 = max_x0
		max_y2 = node.max_y

		min_x3 = max_x0
		min_y3 = max_y0
		max_x3 = node.max_y
		max_y3 = node.max_y

		child0 = QuadTreeGenNode(self.next_node_id, min_x0, min_y0, max_x0, max_y0, node.zoom_level+1,
				parent_geom=geom)
		self.next_node_id += 1

		child1 = QuadTreeGenNode(self.next_node_id, min_x1, min_y1, max_x1, max_y1, node.zoom_level+1,
				parent_geom=geom)
		self.next_node_id += 1

		child2 = QuadTreeGenNode(self.next_node_id, min_x2, min_y2, max_x2, max_y2, node.zoom_level+1,
				parent_geom=geom)
		self.next_node_id += 1

		child3 = QuadTreeGenNode(self.next_node_id, min_x3, min_y3, max_x3, max_y3, node.zoom_level+1,
				parent_geom=geom)
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

