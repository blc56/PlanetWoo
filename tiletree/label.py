##\file __init__.py Main classes for the tiletree.label module. 
import StringIO
import mapscript
import cairo

import tiletree

def position_label(seed_point, min_x, min_y, max_x, max_y, label_spacing, label_width, label_height):
	#TODO: implement "virtual grid system"
	if(seed_point.x >= min_x and seed_point.x <= max_x and seed_point.y >= min_y and seed_point.y <= max_y):
		return (seed_point.x,  seed_point.y, seed_point.x + label_width, seed_point.y + label_height)
	return None

#def collision_check(

class LabelRenderer:
	def __init__(self, mapfile_string, feature_storage_manager,label_spacing=1024,
		img_w=256, img_h=256):
		self.mapfile = mapscript.fromstring(mapfile_string)
		self.feature_storage_manager = feature_storage_manager
		self.label_spacing = label_spacing
		self.img_w = img_w
		self.img_h = img_h

	def tile_info(self, node, check_full=True):
		#return self.feature_storage_manager.fetch_info(node.zoom_level, node.tile_x, node.tile_y)
		return (False, False, False)

	def render_label(self, surface, label_text, img_x, img_y):
		context = cairo.Context(surface)
		context.set_line_width(20)
		context.new_path()
		context.move_to(img_x, img_y)
		context.line_to(img_x + 20, img_y + 20)
		context.set_source_rgba(1.0, 0, 0, 1.0)
		context.stroke()

	def render(self, node):
		rect = mapscript.rectObj(node.min_x, node.min_y, node.max_x, node.max_y)
		self.mapfile.queryByRect(rect)
		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.img_w, self.img_h)

		for x in range(self.mapfile.numlayers):
			layer = self.mapfile.getLayer(x)
			layer.open()
			num_results = layer.getNumResults()
			for f in range(num_results):
				result = layer.getResult(f)
				shape = layer.getShape(result)
				seed_point = shape.getCentroid()
				#TODO: calculate label width!!!
				label_extent = position_label(seed_point, node.min_x, node.min_y, node.max_x, node.max_y,
					self.label_spacing, 100, 100)
				if(not label_extent):
					continue
				img_x, img_y = tiletree.geo_coord_to_img(label_extent[0], label_extent[1],
						self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)
				#TODO: check collisions from other labels and reposition
				#TODO: actually render the label
				#print img_x, img_y
				self.render_label(surface, "Test", img_x, img_y)

			layer.close()

		self.mapfile.freeQuery()

		img_bytes = StringIO.StringIO()
		img_id = tiletree.build_node_id(node.zoom_level, node.tile_x, node.tile_y)
		surface.write_to_png(img_bytes)
		return (img_id, img_bytes)

