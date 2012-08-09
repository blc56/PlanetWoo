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

			child_image = big_image.crop((min_x, min_y, max_x, max_y))
			child_img_bytes = StringIO.StringIO()
			child_image.save(child_img_bytes, 'png')
			child_images.append(child_img_bytes)

		#re-order things so the coordinates line up
		return child_images

	def flush(self):
		self.backend.flush()

	def store(self, node, img_bytes):
		if((not node.is_blank) and (not node.is_full) ):
			child_images = self.split_img(img_bytes)
		else:
			#if it is a blank or full image, just create
			# copies of the orignal image since it will be the correct size
			child_images = [img_bytes]*(4**self.num_splits)

		child_nodes = [node]
		for x in range(self.num_splits):
			new_child_nodes = []
			while(len(child_nodes) > 0):
				this_node = child_nodes.pop()
				new_child_nodes.extend(this_node.split())
			child_nodes = new_child_nodes

		child_nodes.sort(key=lambda x:(x.tile_x, x.tile_y))

		for node, img in zip(child_nodes, child_images):
			self.backend.store(node, img)

	def fetch(self, zoom_level, x, y):
		self.backend.fetch(self, zoom_level, x, y)

	def close(self):
		self.backend.close()

