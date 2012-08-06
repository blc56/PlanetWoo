##\file mapserver.py render classes for the tiletree module. 
from tiletree import *
import shapely
import shapely.wkt
import shapely.geometry
import time
import mapscript
import tiletree
import Image

class MapServerRenderer(Renderer):
	def __init__(self, mapfile_template, layers, img_w=256, img_h=256, img_buffer=0, min_zoom=0, max_zoom=19,
			cache_fulls=True, srs='EPSG:3857'):
		Renderer.__init__(self, img_w, img_h)
		self.mapfile_template=mapfile_template
		self.layers=layers
		self.img_buffer=img_buffer
		self.min_zoom = min_zoom
		self.max_zoom = max_zoom
		self.cache_fulls=cache_fulls
		self.srs = srs

		#creating a mapfile leaks memory, so only create it once
		template_args = {
			#'wkt': shapely.wkt.dumps(geometry),
			#'shapefile_path' : shapefile_path
		}
		self.mapfile = mapscript.fromstring(self.mapfile_template % template_args)
		self.mapfile.loadOWSParameters(self.build_request(0, 0, 10, 10))

	def tile_info(self, node, check_full=True):
		if(node.zoom_level < self.min_zoom):
			node.is_blank = True
			node.is_leaf = False
			return

		if(node.zoom_level > self.max_zoom):
			node.is_blank = True
			node.is_leaf = True
			return

		node.is_blank = True
		node.is_full = False
		node.is_leaf = True

		#NOTE: we make the assumption here that a full node will contain only
		#one geometry
		#TODO: respect self.layers here
		rect = mapscript.rectObj(node.min_x, node.min_y, node.max_x, node.max_y)
		self.mapfile.queryByRect(rect)
		for layer_name in self.layers:
			layer = self.mapfile.getLayerByName(layer_name)
			layer.open()
			num_results = layer.getNumResults()
			if(num_results > 0 and num_results != 1):
				node.is_blank = False
				node.is_leaf = False
				layer.close()
				#this is a non blank, non full node
				break
			elif(num_results == 1):
				node.is_blank = False
				node.is_leaf = False
				if(check_full):
					result = layer.getResult(0)
					shape = layer.getShape(result)
					bbox_shape = mapscript.shapeObj_fromWKT(
						tiletree.bbox_to_wkt(node.min_x, node.min_y, node.max_x, node.max_y))
					if(shape.contains(bbox_shape)):
						node.is_full=True
						node.is_leaf=True
						layer.close()
						break
			layer.close()

		self.mapfile.freeQuery()

	def cut_img_buffer(self, img_bytes):
		#TODO:XXX: fix this function
		if(self.img_buffer == 0):
			return img_bytes
		buffer_img = Image.open(img_bytes)
		cut_img = buffer_img.crop( (self.img_buffer, self.img_buffer,
				self.img_w + self.img_buffer, self.img_h + self.img_buffer) )
		cut_img.load()
		cut_bytes = StringIO.StringIO()
		cut_img.save(cut_bytes, 'png')
		return cut_bytes

	def render_normal(self, node):
		if(self.img_buffer > 0):
			expand_x = (self.img_buffer / float(self.img_w)) * (node.max_x - node.min_x)
			expand_y = (self.img_buffer / float(self.img_h)) * (node.max_y - node.min_y)
			self.mapfile.setExtent(node.min_x - expand_x, node.min_y - expand_y,
				node.max_x + expand_x, node.max_y + expand_y)
		else:
			self.mapfile.setExtent(node.min_x, node.min_y, node.max_x, node.max_y)

		#self.mapfile.loadOWSParameters(self.build_request(node.min_x, node.min_x, node.max_x, node.max_y))
		img = self.mapfile.draw()

		img_id = build_node_id(node.zoom_level, node.tile_x, node.tile_y)
		img_bytes = self.cut_img_buffer(StringIO.StringIO(img.getBytes()))
		result =  (img_id, img_bytes)

		return result

	def render(self, node):
		if(node.is_blank):
			if(self.blank_img_bytes == None):
				self.blank_img_bytes = self.render_normal(node)[1]
			return (self.blank_img_id, self.blank_img_bytes)
		elif(node.is_full and self.cache_fulls):
			if(self.full_img_bytes == None):
				self.full_img_bytes = self.render_normal(node)[1]
			return (self.full_img_id, self.full_img_bytes)
		return self.render_normal(node)

	def build_request(self, min_x, min_y, max_x, max_y):
		wms_req = mapscript.OWSRequest()
		wms_req.setParameter('MODE', 'tile')
		wms_req.setParameter('VERSION', '1.1.1')
		wms_req.setParameter('FORMAT', 'image/png')
		wms_req.setParameter('WIDTH', str(self.img_w + self.img_buffer*2))
		wms_req.setParameter('HEIGHT', str(self.img_h + self.img_buffer*2))
		wms_req.setParameter('SRS', self.srs)
		wms_req.setParameter('REQUEST', 'GetMap')
		wms_req.setParameter('BBOX', ','.join(str(x) for x in [min_x, min_y, max_x, max_y]))
		wms_req.setParameter('LAYERS', ','.join(self.layers) )

		return wms_req

