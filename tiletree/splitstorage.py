##\file splitstorage.py storage classes for the tiletree module. 
import tiletree
import os
import Image
import itertools
import StringIO

class SplitStorageManager:
	def __init__(self, backend_storage_manager, num_splits):
		self.backend = backend_storage_manager
		self.num_splits = num_splits
		self.next_node_id = 0
		self.next_img_id = 0
		self.cutter = tiletree.NullGeomCutter()
		self.blank_img_id = None
		self.full_img_id = None

	def split_img(self, img_bytes):
		big_image = Image.open(img_bytes)
		
		tile_range = 2**self.num_splits
		x_pixels_per_tile = big_image.size[0] / tile_range
		y_pixels_per_tile = big_image.size[1] / tile_range
		tile_coords = itertools.product(range(tile_range), repeat=2)
		child_images=[]
		for tile_x, tile_y in tile_coords:
			min_x = tile_x * x_pixels_per_tile
			min_y = tile_y * y_pixels_per_tile
			max_x = min_x +  x_pixels_per_tile
			max_y = min_y +  y_pixels_per_tile

			child_images.append(big_image.crop((min_x, min_y, max_x, max_y)))

		#re-order things so the coordinates line up
		return (child_images[1], child_images[3], child_images[0], child_images[2])

	def split_node(self, node):
		node.child_0 = self.next_node_id
		self.next_node_id += 1
		node.child_1 = self.next_node_id
		self.next_node_id += 1
		node.child_2 = self.next_node_id
		self.next_node_id += 1
		node.child_3 = self.next_node_id
		self.next_node_id += 1

		ret_nodes =  node.split(self.cutter)
		ret_nodes[0].image_id = self.next_img_id
		self.next_img_id += 1
		ret_nodes[1].image_id = self.next_img_id
		self.next_img_id += 1
		ret_nodes[2].image_id = self.next_img_id
		self.next_img_id += 1
		ret_nodes[3].image_id = self.next_img_id
		self.next_img_id += 1

		return ret_nodes

	def store(self, node, img_bytes):
		##TODO: something else here!!
		if(node.is_blank):
			if(self.blank_img_id == None):
				self.blank_img_id = self.next_img_id
				self.next_img_id +=1
			node.image_id = self.blank_img_id
			return self.backend.store(node, img_bytes)
		elif(node.is_full):
			if(self.full_img_id == None):
				self.full_img_id = self.next_img_id
				self.next_img_id +=1
			node.image_id = self.full_img_id
			return self.backend.store(node, img_bytes)

		child_images = self.split_img(img_bytes)

		child_nodes = [node]
		for x in range(self.num_splits):
			this_node = child_nodes.pop()
			child_nodes.extend(self.split_node(this_node))

		for node, img in zip(child_nodes, child_images):
			child_img_bytes = StringIO.StringIO()
			img.save(child_img_bytes, 'png')
			self.backend.store(node, child_img_bytes)

	def lookup_tile(self, zoom_level, x, y):
		self.backend.lookup_tile(self, zoom_level, x, y)

	def close(self):
		self.backend.close()

