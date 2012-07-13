##\file composite.py 
import Image
import StringIO

class TileCompositor:
	def __init__(self, storage_managers):
		self.storage_managers = storage_managers

	def fetch(self, zoom_level, x, y):
		print self.storage_managers
		#fetch a tile from each layer
		tiles = ( s.fetch(zoom_level, x, y) for s in self.storage_managers )

		#then composite those layers together
		output_tile = None
		for tile in tiles:
			if(output_tile == None):
				output_tile = Image.open(tile)
				continue
			new_tile = Image.open(tile)
			output_tile.paste(new_tile, (0, 0), new_tile)

		output_bytes = StringIO.StringIO()
		output_tile.save(output_bytes, format='PNG')

		return StringIO.StringIO(output_bytes.getvalue())

