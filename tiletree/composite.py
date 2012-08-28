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

##\file composite.py 
import StringIO
import tiletree
import cairo
#import Image

class RenderInfo:
	def __init__(self, name, storage_manager, renderer, cutter, check_full, start_zoom=None,
			stop_zoom=None, label_col_index=None):
		self.name = name
		self.storage_manager = storage_manager
		self.renderer = renderer
		self.cutter = cutter
		self.check_full = check_full
		self.start_zoom = start_zoom
		self.stop_zoom = stop_zoom
		self.label_col_index = label_col_index

class TileCompositor:
	def __init__(self, render_info_dict, layer_order, extent=(0, 0, 0, 0)):
		self.render_infos = render_info_dict
		self.extent = extent
		self.layer_order = layer_order

	def fetch(self, zoom_level, x, y, layers, do_palette=True):
		tile_generator = ( self.render_infos[l].storage_manager.fetch(zoom_level, x, y)
				for l in layers )
		return self.fetch_helper(tile_generator, do_palette)


	def dynamic_fetch(self, zoom_level, x, y, layers, do_palette=True):
		#use a list to preserve side effects
		label_geoms = [None]
		#we call fetch_render() for _every_ layer in self.render_infos
		#we want to render every layer, even if they aren't all going to be returned so that interlayer dependencies
		#are preserved (think labels...)
		tile_generator = (self.fetch_render(zoom_level, x, y, self.render_infos[l], self.extent, label_geoms, layers)
			for l in self.layer_order)
		return self.fetch_helper(tile_generator, do_palette)

	def fetch_render(self, zoom_level, x, y, render_info, extent, label_geoms, layers):
		if((render_info.start_zoom != None and render_info.start_zoom > zoom_level) or
				(render_info.stop_zoom != None and render_info.stop_zoom < zoom_level) ):
			return None
		storage_manager = render_info.storage_manager
		renderer = render_info.renderer
		cutter = render_info.cutter
		try:
			result =  storage_manager.fetch(zoom_level, x, y)
			if(render_info.name in layers):
				return result
			return None
		except tiletree.TileNotFoundException:
			bbox = tiletree.tile_coord_to_bbox(zoom_level, x, y, extent)
			geom = cutter.cut(bbox[0], bbox[1], bbox[2], bbox[3])
			node = tiletree.QuadTreeGenNode(None,  bbox[0], bbox[1], bbox[2], bbox[3], zoom_level, None,
				geom=geom, tile_x=x, tile_y=y, label_geoms=label_geoms[0])
			renderer.tile_info(node, check_full=render_info.check_full)
			img_bytes = renderer.render(node)[1]
			storage_manager.store(node, img_bytes)
			label_geoms[0] = node.label_geoms
			if(render_info.name in layers):
				return StringIO.StringIO(img_bytes.getvalue())
			return None

	def fetch_helper(self, tile_generator, do_palette=True):
		output_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 256, 256)
		output_context = cairo.Context(output_surface)
		for tile in tile_generator:
			if(tile == None):
				continue

			tile_img = cairo.ImageSurface.create_from_png(tile)

			output_context.set_source_surface(tile_img, 0, 0)
			output_context.paint()

		output_bytes = StringIO.StringIO()
		output_surface.write_to_png(output_bytes)

		if(do_palette):
			return tiletree.palette_png_bytes(StringIO.StringIO(output_bytes.getvalue()))
		return StringIO.StringIO(output_bytes.getvalue())

