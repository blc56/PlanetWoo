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

##\file csvstorage.py storage classes for the tiletree module. 
import planetwoo.tiletree as tiletree
import os
import shapely.wkt

class CSVStorageManager:
	def __init__(self, tree_file, image_file=None,
			fields=['node_id', 'zoom_level', 'tile_x', 'tile_y', 'image_id', 'is_leaf', 'is_blank',
				'is_full', 'metadata'], img_w=256, img_h=256):
		self.tree_file = tree_file
		self.image_file = image_file
		self.fields = fields
		self.img_w = float(img_w)
		self.img_h = float(img_h)
		self.blank_img_id = None
		self.full_img_id = None

		self.open()

	def open(self):
		self.tree_file.write(','.join(self.fields))
		self.tree_file.write('\n')

		if(self.image_file):
			self.image_file.write(','.join(['image_id', 'image_fn']))
			self.image_file.write('\n')

	def flush(self):
		if(self.tree_file):
			self.tree_file.flush()
		if(self.image_file):
			self.image_file.flush()


	def lookup_tile(self, zoom_level, x, y):
		raise Exception("Not implemented")

	def store_image(self, node, img_bytes):
		if(self.image_file == None):
			return
		if(node.is_blank and node.image_id == self.blank_img_id):
			#we've already stored the blank image
			if(self.blank_img_id != None):
				return
			#we haven't stored the blank image yes
			self.blank_img_id = node.image_id
		elif(node.is_full and node.image_id == self.full_img_id):
			#we've already stored the full image
			if(self.full_img_id != None):
				return
			#we haven't stored the full image yes
			self.full_img_id = node.image_id

		self.image_file.write(','.join([str(node.image_id), tiletree.encode_img_bytes(img_bytes.getvalue())]))
		self.image_file.write('\n')

	def store(self, node, img_bytes):
		csv_fields = []
		for f in self.fields:
			if(f != 'geom'):
				csv_fields.append(repr(getattr(node,f)))
			else:
				#simplify the geometry appropriately for this bounding box and
				#tile size before storing it
				simplify_factor = min(abs(node.max_x - node.min_x)/self.img_w,
						abs(node.max_y - node.min_y)/self.img_h)
				simplify_factor /= 2.0
				geom = node.geom.simplify(simplify_factor, preserve_topology=False)
				csv_fields.append('"' + shapely.wkt.dumps(geom) + '"')

		self.tree_file.write(','.join(csv_fields))
		self.tree_file.write('\n')

		self.store_image(node, img_bytes)

	def close(self):
		if(self.tree_file):
			self.tree_file.close()
			self.tree_file = None
		if(self.image_file):
			self.image_file.close()
			self.image_file = None

