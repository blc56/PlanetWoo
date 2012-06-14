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
		self.cutter = tiletree.NullGeomCutter()

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
		return child_images

	def store(self, node, img_bytes):
		if(node.is_blank or node.is_full):
			return self.backend.store(node, img_bytes)

		child_images = self.split_img(img_bytes)

		child_nodes = [node]
		for x in range(self.num_splits):
			new_child_nodes = []
			while(len(child_nodes) > 0):
				this_node = child_nodes.pop()
				new_child_nodes.extend(this_node.split())
			child_nodes = new_child_nodes

		for node, img in zip(child_nodes, child_images):
			child_img_bytes = StringIO.StringIO()
			img.save(child_img_bytes, 'png')
			self.backend.store(node, child_img_bytes)

	def lookup_tile(self, zoom_level, x, y):
		self.backend.lookup_tile(self, zoom_level, x, y)

	def close(self):
		self.backend.close()

