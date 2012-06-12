##\file csvstorage.py storage classes for the tiletree module. 
import tiletree
import os

class CSVStorageManager:
	def __init__(self, tree_file, image_file, image_prefix='images/', image_suffix='.png',
			fields=['node_id', 'zoom_level', 'tile_x', 'tile_y', 'image_id', 'is_leaf', 'is_blank',
				'is_full']):
		self.tree_file = tree_file
		self.image_file = image_file
		self.image_prefix = image_prefix
		self.image_suffix = image_suffix
		self.fields = fields

		self.tree_file.write(','.join(self.fields))
		self.tree_file.write('\n')

		self.image_file.write(','.join(['image_id', 'image_fn']))
		self.image_file.write('\n')

	def lookup_tile(self, zoom_level, x, y):
		raise Exception("Not implemented")

	def _get_storage_path(self, node):
		return self.image_prefix + repr(node.image_id) + self.image_suffix

	def store(self, node, img_bytes):
		self.tree_file.write(','.join(repr(getattr(node, x)) for x in self.fields))
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
