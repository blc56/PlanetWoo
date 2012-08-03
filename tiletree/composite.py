##\file composite.py 
import Image
import StringIO
import tiletree

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

	def fetch(self, zoom_level, x, y, layers):
		tile_generator = ( self.render_infos[l].storage_manager.fetch(zoom_level, x, y)
				for l in layers )
		return self.fetch_helper(tile_generator)



	def dynamic_fetch(self, zoom_level, x, y, layers):
		#use a list to preserve side effects
		label_geoms = [None]
		#we call fetch_render() for _every_ layer in self.render_infos
		#we want to render every layer, even if they aren't all going to be returned so that interlayer dependencies
		#are preserved (think labels...)
		tile_generator = (self.fetch_render(zoom_level, x, y, self.render_infos[l], self.extent, label_geoms, layers)
			for l in self.layer_order)
		return self.fetch_helper(tile_generator)

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
			storage_manager.store_node(node)
			storage_manager.store_image(node, img_bytes)
			storage_manager.flush()
			label_geoms[0] = node.label_geoms
			if(render_info.name in layers):
				return StringIO.StringIO(img_bytes.getvalue())
			return None

	def fetch_helper(self, tile_generator):
		#TODO: use imagemagick to see if paletting is faster
		#then composite those layers together
		output_tile = None
		for tile in tile_generator:
			if(tile == None):
				continue
			if(output_tile == None):
				output_tile = Image.open(tile)
				#output_tile = output_tile.convert('RGBA')
				continue
			new_tile = Image.open(tile)
			#new_tile = new_tile.convert('RGBA')
			output_tile.paste(new_tile, (0, 0), new_tile)

		#output_tile = output_tile.convert('RGB')
		#output_tile = output_tile.convert('P', palette=Image.ADAPTIVE, colors=256)
		output_bytes = StringIO.StringIO()
		output_tile.save(output_bytes, format='PNG')

		return StringIO.StringIO(output_bytes.getvalue())

