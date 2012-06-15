##\file mapserver.py render classes for the tiletree module. 
from tiletree import *
import shapely
import shapely.wkt
import shapely.geometry
from psycopg2 import *
import time

class MapServerRenderer(Renderer):
	def __init__(self, mapfile_template, layers, img_w=256, img_h=256, img_prefix='images/'):
		Renderer.__init__(self, img_w, img_h, img_prefix)
		self.mapfile_template=mapfile_template
		self.layers=layers

		#creating a mapfile leaks memory, so only create it once
		template_args = {
			#'wkt': shapely.wkt.dumps(geometry),
			#'shapefile_path' : shapefile_path
		}
		self.mapfile = mapscript.fromstring(self.mapfile_template % template_args)

	def render_normal(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level, tile_x, tile_y):
		#print zoom_level, tile_x, tile_y, min_x, min_y, max_x, max_y
		self.mapfile.setExtent(min_x, min_y, max_x, max_y)
		img = self.mapfile.draw()

		img_id = build_node_id(zoom_level, tile_x, tile_y)
		result =  (img_id,
				StringIO.StringIO(img.getBytes()))
		return result

