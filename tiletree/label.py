##\file __init__.py Main classes for the tiletree.label module. 
import StringIO
import mapscript
import cairo
import math

import tiletree

ALMOST_ZERO = float(1e-10)

def bbox_check(label_bbox, tile_bbox):
	if(label_bbox[0] <= tile_bbox[2] and label_bbox[2] >= tile_bbox[0] and
		label_bbox[1] <= tile_bbox[3] and label_bbox[3] >= tile_bbox[1]):
		return True
	return False

class LabelRenderer:
	def __init__(self, mapfile_string, feature_storage_manager, label_col_index, map_extent,
			min_zoom=0, max_zoom=19,
			label_spacing=1024, img_w=256, img_h=256, tile_buffer=256, font='Utopia', font_size=12,
			point_labels=True):
		self.mapfile = mapscript.fromstring(mapfile_string)
		self.feature_storage_manager = feature_storage_manager
		self.label_col_index = label_col_index
		self.map_extent = map_extent
		self.label_spacing = label_spacing
		self.img_w = img_w
		self.img_h = img_h
		self.tile_buffer = tile_buffer
		self.font = font
		self.font_size = font_size
		self.min_zoom = min_zoom
		self.max_zoom = max_zoom
		self.point_labels = point_labels

	def tile_info(self, node, check_full=True):
		return (False, False, False)

	def render_label(self, context, label_text, img_x, img_y, img_max_x, img_max_y, color):
		context.move_to(img_x, img_y)
		context.text_path(label_text)
		context.fill()

		context.set_line_width(2)
		#context.new_path()
		context.move_to(img_x, img_y)
		context.line_to(img_max_x, img_y)
		context.line_to(img_max_x, img_max_y)
		context.line_to(img_x, img_max_y)
		context.line_to(img_x, img_y)
		#context.set_source_rgba(1, 0, 0, .5)
		context.set_source_rgba(*color)
		context.stroke()

	def get_label_size(self, surface, label_text):
		context = cairo.Context(surface)
		font_face = context.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		context.set_font_face(font_face)
		context.set_font_size(self.font_size)
		text_extents = context.text_extents(label_text)
		return (context, text_extents[2], text_extents[3])

	def build_image(self, surface, node):
		img_bytes = StringIO.StringIO()
		img_id = tiletree.build_node_id(node.zoom_level, node.tile_x, node.tile_y)
		surface.write_to_png(img_bytes)
		return (img_id, img_bytes)

	#returns (is_in_tile, bbox)
	def position_label(self, shape, node, img_w, img_h, label_spacing, label_width, label_height):
		seed_point = shape.getCentroid()

		x_scale = (node.max_x - node.min_x) / float(img_w)
		y_scale = (node.max_y - node.min_y) / float(img_h)
		x_repeat_interval = label_spacing * x_scale
		y_repeat_interval = label_spacing * y_scale
		label_geo_w = label_width * x_scale * .5
		label_geo_h = label_height * y_scale * .5

		x_mid = (node.max_x - node.min_x) / 2.0
		y_mid = (node.max_y - node.min_y) / 2.0
		x_spaces = math.floor((node.max_x - seed_point.x)/float(x_repeat_interval) + .5)
		y_spaces = math.floor((node.max_y - seed_point.y)/float(y_repeat_interval) + .5)

		ghost_x = seed_point.x + x_spaces * x_repeat_interval
		ghost_y = seed_point.y + y_spaces * y_repeat_interval

		label_geo_bbox = (ghost_x - label_geo_w, ghost_y - label_geo_h,
				ghost_x + label_geo_w, ghost_y + label_geo_h) 

		is_in_tile = False
		if(bbox_check(label_geo_bbox, (node.min_x, node.min_y, node.max_x, node.max_y))):
			is_in_tile = True

		label_geo_bbox_shape = mapscript.shapeObj.fromWKT(tiletree.bbox_to_wkt(*label_geo_bbox))
		if(self.point_labels and (x_spaces < 1 and y_spaces < 1) ):
			return (is_in_tile, label_geo_bbox)
		elif(shape.contains(label_geo_bbox_shape) ):
			return (is_in_tile, label_geo_bbox)
		return None

	def collision_check(self, node, check_bbox, label_bboxes):
		for l in label_bboxes:
			if(bbox_check(l, check_bbox)):
				return True
		return False

	def render(self, node):
		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.img_w, self.img_h)
		#convert from a pixel buffer distance to an image buffer distance
		x_scale = (node.max_x - node.min_x) / float(self.img_w) 
		y_scale = (node.max_y - node.min_y) / float(self.img_h)
		x_buffer = x_scale * self.tile_buffer
		y_buffer = y_scale * self.tile_buffer

		label_bboxes = []

		rect = mapscript.rectObj(node.min_x - x_buffer, node.min_y - y_buffer,
				node.max_x + x_buffer, node.max_y + y_buffer)
		self.mapfile.queryByRect(rect)

		for x in range(self.mapfile.numlayers):
			layer = self.mapfile.getLayer(x)
			layer.open()
			num_results = layer.getNumResults()
			for f in range(num_results):
				result = layer.getResult(f)
				shape = layer.getShape(result)
				label_text = unicode(shape.getValue(self.label_col_index), 'latin_1')
				context, label_width, label_height = self.get_label_size(surface, label_text)

				pos_results = self.position_label(shape, node, self.img_w, self.img_h, self.label_spacing,
						label_width, label_height)

				if(pos_results == None):
					continue

				is_in_tile, label_extent = pos_results

				color = (1, 0, 0, 1)
				if(self.collision_check(node, label_extent, label_bboxes)):
					color = (0, 1, 0, 1)
					continue

				label_bboxes.append(label_extent)
				if(not is_in_tile):
					continue

				img_x, img_y = tiletree.geo_coord_to_img(label_extent[0], label_extent[1],
						self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)
				img_max_x, img_max_y = tiletree.geo_coord_to_img(label_extent[2], label_extent[3],
						self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)

				#TODO: add fontconfig with zoom level range and other options
				self.render_label(context, label_text, img_x, img_y, img_max_x, img_max_y, color)

			layer.close()

		self.mapfile.freeQuery()

		return self.build_image(surface, node)

