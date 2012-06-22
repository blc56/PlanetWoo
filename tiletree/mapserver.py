##\file mapserver.py render classes for the tiletree module. 
from tiletree import *
import shapely
import shapely.wkt
import shapely.geometry
import time
import mapscript

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
		#aparrently, setExtent() is not the same as whatever the BBOX parameter does
		#once I figure out the equivalent swig call we can get rid of the request processing
		#zoomRectangle() maybe?
		self.mapfile.loadOWSParameters(self.build_request(min_x, min_y, max_x, max_y))
		#self.mapfile.setExtent(min_x, min_y, max_x, max_y)

		img = self.mapfile.draw()

		img_id = build_node_id(zoom_level, tile_x, tile_y)
		result =  (img_id, StringIO.StringIO(img.getBytes()))

		return result

	def render(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level, tile_x, tile_y):
		if(is_blank):
			if(self.blank_img_bytes == None):
				self.blank_img_bytes = self.render_normal(geometry, is_blank, 
					is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level,
					tile_x, tile_y)[1]
			return (self.blank_img_id, self.blank_img_bytes)
		elif(is_full):
			if(self.full_img_bytes == None):
				self.full_img_bytes = self.render_normal(geometry, is_blank, 
					is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level,
					tile_x, tile_y)[1]
			return (self.full_img_id, self.full_img_bytes)
		return self.render_normal(geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level, tile_x, tile_y)

	def build_request(self, min_x, min_y, max_x, max_y):
		wms_req = mapscript.OWSRequest()
		wms_req.setParameter('MODE', 'WMS')
		wms_req.setParameter('VERSION', '1.1.1')
		wms_req.setParameter('FORMAT', 'image/png')
		wms_req.setParameter('WIDTH', str(self.img_w))
		wms_req.setParameter('HEIGHT', str(self.img_h))
		#wms_req.setParameter('WIDTH', '2048')
		#wms_req.setParameter('HEIGHT', '2048')
		wms_req.setParameter('SRS', 'EPSG:3857')
		wms_req.setParameter('REQUEST', 'GetMap')
		wms_req.setParameter('BBOX', ','.join(str(x) for x in [min_x, min_y, max_x, max_y]))
		wms_req.setParameter('LAYERS', ','.join(self.layers) )

		return wms_req

