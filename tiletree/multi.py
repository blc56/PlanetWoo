##\file __init__.py Main classes for the tiletree.multi_render module. 
import copy

import tiletree

class MultiGeom:
	def __init__(self, num_layers, parent_geom=None):
		self.geoms = [None] * num_layers
		self.leaf_reached = [False] * num_layers
		if(parent_geom):
			self.leaf_reached = copy.copy(parent_geom.leaf_reached)


class MultiCutter(tiletree.NullGeomCutter):
	def __init__(self, cutters):
		self.cutters = cutters

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		if(parent_geom == None):
			parent_geom = MultiGeom(len(self.cutters), parent_geom)
		result = MultiGeom(len(self.cutters), parent_geom)
		result.geoms = [c.cut(min_x, min_y, max_x, max_y, p) for c,p in zip(self.cutters, parent_geom.geoms)]
		return result

class MultiRenderer:
	def __init__(self, renderers):
		self.renderers = renderers

	def tile_info(self, node, check_full=True):
		is_blank = True
		is_full = True
		is_leaf = True

		if(node.geom == None):
			node.geom = MultiGeom(len(self.renderers))

		r_iter = -1
		for renderer in self.renderers:
			r_iter += 1

			if(node.geom.leaf_reached == 'blank'):
				is_full = False
				continue

			elif(node.geom.leaf_reached == 'full'):
				is_blank = False
				continue

			tmp_node = copy.copy(node)
			tmp_node.geom = node.geom.geoms[r_iter]
			renderer.tile_info(tmp_node, check_full)
			if(not tmp_node.is_blank):
				is_blank = False
			if(not tmp_node.is_leaf):
				is_leaf = False
			if(not tmp_node.is_full):
				is_full = False

			node.label_geoms = tmp_node.label_geoms

		node.is_blank = is_blank
		node.is_full = is_full
		node.is_leaf = is_leaf

	def render(self, node):
		is_blank = True
		is_full = True
		is_leaf = True

		img_ids = []
		img_bytes = []

		r_iter = -1
		for renderer in self.renderers:
			r_iter += 1
			if(node.geom.leaf_reached[r_iter] != False):
				img_ids.append(None)
				img_bytes.append(None)
				continue

			tmp_node = copy.copy(node)
			tmp_node.geom = node.geom.geoms[r_iter]

			this_id, this_bytes = renderer.render(tmp_node)

			img_ids.append(this_id)
			img_bytes.append(this_bytes)

			if(not tmp_node.is_blank):
				is_blank = False
			if(not tmp_node.is_leaf):
				is_leaf = False
			if(not tmp_node.is_full):
				is_full = False

			if(tmp_node.is_blank and tmp_node.is_leaf):
				node.geom.leaf_reached[r_iter] = 'blank'
			if(tmp_node.is_full and tmp_node.is_leaf):
				node.geom.leaf_reached[r_iter] = 'full'

			node.label_geoms = tmp_node.label_geoms

		node.is_blank = is_blank
		node.is_full = is_full
		node.is_leaf = is_leaf
		node.image_id = img_ids

		return (node.image_id, img_bytes)

class MultiStorageManager:
	def __init__(self, storage_managers):
		self.storage_managers = storage_managers
		
	def store(self, node, img_bytes):
		s_iter = -1

		for storage_manager in self.storage_managers:
			s_iter += 1
			if(img_bytes[s_iter] == None):
				continue

			tmp_node = copy.copy(node)
			tmp_node.image_id = node.image_id[s_iter]

			storage_manager.store(tmp_node, img_bytes[s_iter])


	def flush(self):
		for storage_manager in self.storage_managers:
			storage_manager.flush()

