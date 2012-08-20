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

##\file mapserver.py render classes for the tiletree module. 
from tiletree import *
import shapely
import shapely.wkt
import shapely.geometry
import time
import mapscript
import tiletree
import cairo

class MapServerRenderer(Renderer):
	def __init__(self, mapfile_template, layers, img_w=256, img_h=256, img_buffer=0, min_zoom=0, max_zoom=19,
			cache_fulls=True, srs='EPSG:3857', trust_cutter=False, tile_buffer=0,
			info_cache_name=None, skip_info=False):
		Renderer.__init__(self, img_w, img_h, info_cache_name=info_cache_name)
		self.mapfile_template=mapfile_template
		self.layers=layers
		self.img_buffer=img_buffer
		self.min_zoom = min_zoom
		self.max_zoom = max_zoom
		self.cache_fulls=cache_fulls
		self.srs = srs
		self.trust_cutter = trust_cutter
		self.tile_buffer = tile_buffer
		self.skip_info = skip_info

		#creating a mapfile leaks memory, so only create it once
		template_args = {
			#'wkt': shapely.wkt.dumps(geometry),
			#'shapefile_path' : shapefile_path
		}
		self.mapfile = mapscript.fromstring(self.mapfile_template % template_args)
		self.mapfile.loadOWSParameters(self.build_request(0, 0, 10, 10))

	def tile_info(self, node, check_full=True):
		if(self.skip_info):
			return

		if(self.info_cache != None):
			cache_info = self.info_cache.get_node_info(node.node_id)
			if(cache_info != None):
				node.__dict__.update(cache_info)
				return

		#if the user is not uing a NullGeomCutter, than
		#user the default tile_info() behavior
		if(self.trust_cutter):
			Renderer.tile_info(self, node, check_full)
			self.cache_tile_info(node)
			return

		if(node.zoom_level > self.max_zoom):
			node.is_blank = True
			node.is_leaf = True
			self.cache_tile_info(node)
			return

		if(node.zoom_level < self.min_zoom):
			node.is_blank = True
			node.is_leaf = False
			self.cache_tile_info(node)
			return

		node.is_blank = True
		node.is_full = False
		node.is_leaf = True

		#NOTE: we make the assumption here that a full node will contain only
		#one geometry

		#useful for line layers where the drawn line would actually be thicker
		#and enter a tile where the line itself wouldn't
		x_buffer = 0
		y_buffer = 0
		if(self.tile_buffer > 0):
			x_scale = (node.max_x - node.min_x) / float(self.img_w) 
			y_scale = (node.max_y - node.min_y) / float(self.img_h)
			x_buffer = x_scale * self.tile_buffer
			y_buffer = y_scale * self.tile_buffer

		rect = mapscript.rectObj(node.min_x - x_buffer, node.min_y - y_buffer,
				node.max_x + x_buffer, node.max_y + y_buffer)

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
					bbox_shape = self.mapfile.extent.toPolygon()
					if(shape.contains(bbox_shape)):
						node.is_full=True
						node.is_leaf=True
						layer.close()
						break
			layer.close()

		self.mapfile.freeQuery()

		self.cache_tile_info(node)
		
	def cut_img_buffer(self, img_bytes):
		if(self.img_buffer == 0):
			return img_bytes

		buffer_img = cairo.ImageSurface.create_from_png(img_bytes)
		output_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.img_w, self.img_h)
		output_context = cairo.Context(output_surface)

		#output_context.set_antialias(cairo.ANTIALIAS_GRAY)
		output_context.set_operator(cairo.OPERATOR_SOURCE)
		output_context.set_source_surface(buffer_img, -self.img_buffer, -self.img_buffer)
		output_context.rectangle(0, 0, self.img_w, self.img_h)
		output_context.fill()

		output_bytes = StringIO.StringIO()
		output_surface.write_to_png(output_bytes)

		return tiletree.palette_png_bytes(StringIO.StringIO(output_bytes.getvalue()))

	def render_normal(self, node):
		if(self.img_buffer > 0):
			expand_x = (self.img_buffer / float(self.img_w)) * (node.max_x - node.min_x)
			expand_y = (self.img_buffer / float(self.img_h)) * (node.max_y - node.min_y)
			self.mapfile.setExtent(node.min_x - expand_x, node.min_y - expand_y,
				node.max_x + expand_x, node.max_y + expand_y)
		else:
			self.mapfile.setExtent(node.min_x, node.min_y, node.max_x, node.max_y)

		#print node.zoom_level, self.mapfile.scaledenom

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

