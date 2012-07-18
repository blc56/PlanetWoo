##\file composite.py 
import Image
import StringIO
import tiletree

class TileCompositor:
	def __init__(self, storage_managers, renderers=[], cutters=[], extent=(0, 0, 0, 0)):
		self.storage_managers = storage_managers
		self.renderers = renderers
		self.cutters = cutters
		self.extent = extent

	def fetch(self, zoom_level, x, y):
		return self.fetch_helper(( s.fetch(zoom_level, x, y) for s in self.storage_managers ) )

	def dynamic_fetch(self, zoom_level, x, y):
		tile_generator = (self.fetch_render(zoom_level, x, y, s[0], s[1], s[2], self.extent)
			for s in zip(self.storage_managers, self.renderers, self.cutters) )
		return self.fetch_helper(tile_generator)

	def fetch_render(self, zoom_level, x, y, storage_manager, renderer, cutter, extent):
		#try:
			#return storage_manager.fetch(zoom_level, x, y)
		#except tiletree.TileNotFoundException:
			bbox = tiletree.tile_coord_to_bbox(zoom_level, x, y, extent)
			geom = cutter.cut(bbox[0], bbox[1], bbox[2], bbox[3])
			is_blank, is_full, is_leaf = renderer.tile_info(geom, bbox[0], bbox[1], bbox[2], bbox[3], zoom_level)
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

