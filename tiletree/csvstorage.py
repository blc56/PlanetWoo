##\file csvstorage.py storage classes for the tiletree module. 
import tiletree
import os
import shapely.wkt
from psycopg2 import *

class CSVStorageManager:
	def __init__(self, tree_file, image_file=None, image_prefix='images/', image_suffix='.png',
			fields=['node_id', 'zoom_level', 'tile_x', 'tile_y', 'image_id', 'is_leaf', 'is_blank',
				'is_full'], img_w=256, img_h=256):
		self.tree_file = tree_file
		self.image_file = image_file
		self.image_prefix = image_prefix
		self.image_suffix = image_suffix
		self.fields = fields
		self.img_w = float(img_w)
		self.img_h = float(img_h)

		self.tree_file.write(','.join(self.fields))
		self.tree_file.write('\n')

		if(self.image_file):
			self.image_file.write(','.join(['image_id', 'image_fn']))
			self.image_file.write('\n')

	def lookup_tile(self, zoom_level, x, y):
		raise Exception("Not implemented")

	def _get_storage_path(self, node):
		return self.image_prefix + repr(node.image_id) + self.image_suffix

	def store_image(self, node, img_bytes):
		if(self.image_file == None):
			return
		img_fn = self._get_storage_path(node)
		if(not os.path.exists(img_fn)):
			#create the image
			open(img_fn, 'w').write(img_bytes.getvalue())
			#also output the information to the csv
			self.image_file.write(','.join([repr(node.image_id), img_fn]))
			self.image_file.write('\n')


	def store(self, node, img_bytes):
		csv_fields = []
		for f in self.fields:
			if(f != 'geom'):
				csv_fields.append(repr(getattr(node,f)))
			else:
				#simplify the geometry appropriatley for this bounding box and
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
		self.tree_file.close()
		if(self.image_file):
			self.image_file.close()

