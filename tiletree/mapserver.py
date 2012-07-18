##\file mapserver.py render classes for the tiletree module. 
from tiletree import *
import shapely
import shapely.wkt
import shapely.geometry
import time
import mapscript
import tiletree

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
		self.mapfile.loadOWSParameters(self.build_request(0, 0, 10, 10))

	def tile_info(self, geometry, min_x, min_y, max_x, max_y, zoom_level, check_full=True):
		is_blank = True
		is_full = False
		is_leaf = True

		#NOTE: we make the assumption here that a full node will contain only
		#one geometry
		rect = mapscript.rectObj(min_x, min_y, max_x, max_y)
		self.mapfile.queryByRect(rect)
		for x in range(self.mapfile.numlayers):
			layer = self.mapfile.getLayer(x)
			layer.open()
			num_results = layer.getNumResults()
			if(num_results > 0 and num_results != 1):
				is_blank = False
				is_leaf = False
				layer.close()
				#this is a non blank, non full node
				break
			elif(num_results == 1):
				is_blank = False
				is_leaf = False
				if(check_full):
					result = layer.getResult(0)
					shape = layer.getShape(result)
					bbox_shape = mapscript.shapeObj_fromWKT(tiletree.bbox_to_wkt(min_x, min_y, max_x, max_y))
					if(shape.contains(bbox_shape)):
						is_full=True
						is_leaf=True
						layer.close()
						break
					#geom = shapely.wkt.loads(shape.toWKT())
					#bbox_geom = shapely.wkt.loads(tiletree.bbox_to_wkt(min_x, min_y, max_x, max_y))
					#if(geom.contains(bbox_geom)):
						#is_full=True
						#is_leaf=True
						#layer.close()
						#break
			layer.close()

		self.mapfile.freeQuery()
		return (is_blank, is_full, is_leaf)

	def render_normal(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level, tile_x, tile_y):
		self.mapfile.setExtent(min_x, min_y, max_x, max_y)
		#self.mapfile.loadOWSParameters(self.build_request(min_x, min_x, max_x, max_y))
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
		wms_req.setParameter('SRS', 'EPSG:3857')
		#TODO make this configurable
		#wms_req.setParameter('SRS', 'EPSG:4326')
		wms_req.setParameter('REQUEST', 'GetMap')
		wms_req.setParameter('BBOX', ','.join(str(x) for x in [min_x, min_y, max_x, max_y]))
		wms_req.setParameter('LAYERS', ','.join(self.layers) )

		return wms_req

