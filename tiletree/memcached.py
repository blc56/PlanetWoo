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

##\file memcached.py 
import StringIO

import tiletree
import memcache

class MCDStorageManager:
	def __init__(self, storage_manager, memcached_servers, layer_order):
		self.storage_manager = storage_manager
		self.layer_order = layer_order
		self.cache = memcache.Client(memcached_servers)

	def compute_layer_key(self, layers):
		#not super efficient, but we'll see how it goes
		return ''.join([str(int(l in layers) ) for l in self.layer_order])

	def fetch(self, zoom_level, x, y, layers):
		cache_id = self.compute_layer_key(layers) + str(tiletree.build_node_id(zoom_level, x, y))
		png_bytes = self.cache.get(cache_id)	
		if(png_bytes == None):
			print 'MISS'
			png_byte_stream = self.storage_manager.fetch(zoom_level, x, y, layers)
			self.cache.set(cache_id, png_byte_stream.getvalue())
			return png_byte_stream

		print 'HIT'
		return StringIO.StringIO(png_bytes)

