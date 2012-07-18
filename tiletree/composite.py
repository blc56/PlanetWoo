##\file composite.py 
import Image
import StringIO
import tiletree

class RenderInfo:
	def __init__(self, storage_manager, renderer, cutter, check_full):
		self.storage_manager = storage_manager
		self.renderer = renderer
		self.cutter = cutter
		self.check_full = check_full

class TileCompositor:
	def __init__(self, render_info_dict, extent=(0, 0, 0, 0)):
		self.render_infos = render_info_dict
		self.extent = extent

	def fetch(self, zoom_level, x, y, layers):
		tile_generator = ( self.render_infos[l].storage_manager.fetch(zoom_level, x, y)
				for l in layers )
		return self.fetch_helper(tile_generator)

	def dynamic_fetch(self, zoom_level, x, y, layers):
		tile_generator = (self.fetch_render(zoom_level, x, y, self.render_infos[l], self.extent)
			for l in layers)
		return self.fetch_helper(tile_generator)

	def fetch_render(self, zoom_level, x, y, render_info, extent):
			storage_manager = render_info.storage_manager
			renderer = render_info.renderer
			cutter = render_info.cutter
		#try:
			#return storage_manager.fetch(zoom_level, x, y)
		#except tiletree.TileNotFoundException:
			bbox = tiletree.tile_coord_to_bbox(zoom_level, x, y, extent)
			geom = cutter.cut(bbox[0], bbox[1], bbox[2], bbox[3])
			is_blank, is_full, is_leaf = renderer.tile_info(geom, bbox[0], bbox[1], bbox[2], bbox[3], zoom_level,
				check_full=render_info.check_full)

			img_bytes = renderer.render(geom, is_blank, is_full, is_leaf, bbox[0], bbox[1], bbox[2], bbox[3],
				zoom_level, x, y)[1]
			node = tiletree.QuadTreeGenNode(None, bbox[0], bbox[1], bbox[2], bbox[3], zoom_level, None,
				is_leaf, is_blank, is_full, None, x, y)
			#storage_manager.store_node(node)
			#storage_manager.store_image(node, img_bytes)
			return StringIO.StringIO(img_bytes.getvalue())

	def fetch_helper(self, tile_generator):
		#then composite those layers together
		output_tile = None
		for tile in tile_generator:
			if(output_tile == None):
				output_tile = Image.open(tile)
				continue
			new_tile = Image.open(tile)
			output_tile.paste(new_tile, (0, 0), new_tile)

		output_bytes = StringIO.StringIO()
		output_tile.save(output_bytes, format='PNG')

		return StringIO.StringIO(output_bytes.getvalue())

