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

##\file fsstorage.py storage classes for the tiletree module. 
import tiletree
import os

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

	def flush(self):
		pass

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


