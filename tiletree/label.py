##\file __init__.py Main classes for the tiletree.label module. 
import StringIO
import mapscript
import cairo
import math
import sys
import shapely
import json
import copy

import tiletree

ALMOST_ZERO = float(1e-10)

def bbox_check(label_bbox, tile_bbox):
	if(label_bbox[0] <= tile_bbox[2] and label_bbox[2] >= tile_bbox[0] and
		label_bbox[1] <= tile_bbox[3] and label_bbox[3] >= tile_bbox[1]):
		return True
	return False

class LabelClass:
	def __init__(self, font='arial', font_size=12, mapserver_query="(1==1)", font_color=(0, 0, 0, 1),
			min_zoom=0, max_zoom=19):
		self.font = font
		self.font_size = font_size
		self.mapserver_query = mapserver_query
		self.font_color = font_color
		self.min_zoom = min_zoom
		self.max_zoom = max_zoom

	def to_dict(self):
		return copy.copy(self.__dict__)

	def from_dict(self, in_dict):
		self.__dict__.update(in_dict)

class LabelRenderer:
	def __init__(self, mapfile_string, storage_manager, label_col_index, mapserver_layers,
			min_zoom=0, max_zoom=19, label_spacing=1024, img_w=256, img_h=256, tile_buffer=256,
			point_labels=False, point_buffer=4, position_attempts=4):
		self.mapfile = mapscript.fromstring(mapfile_string)
		self.storage_manager = storage_manager
		self.label_col_index = label_col_index
		self.mapserver_layers = mapserver_layers
		self.label_spacing = label_spacing
		self.img_w = img_w
		self.img_h = img_h
		self.tile_buffer = tile_buffer
		self.min_zoom = min_zoom
		self.max_zoom = max_zoom
		self.point_labels = point_labels
		self.point_buffer = point_buffer
		self.position_attempts = position_attempts
		self.label_adjustment_max = (self.label_spacing / 2.0) - max(self.img_w, self.img_h)
		if(self.label_adjustment_max < 0):
			raise Exception("Bad parameters")
		self.label_classes = {}

	def add_label_class(self, layer_name, label_class):
		layer_classes = self.label_classes.setdefault(layer_name, [])
		layer_classes.append(label_class)

	def tile_info(self, node, check_full=True):
		if(self.storage_manager == None or not check_full):
			return

		try:
			result = self.storage_manager.fetch_info(node.zoom_level, node.tile_x, node.tile_y)
		except tiletree.TileNotFoundException:
			return

		is_blank, is_full, is_leaf, metadata = result
		if(is_full):
			node.is_full = True
			node.metadata = metadata

	def render_label(self, context, label_text, img_x, img_y, img_max_x, img_max_y, label_class):
		context.move_to(img_x, img_y)
		context.text_path(label_text)
		context.fill()

		#TODO: XXX BLC testing
		context.set_line_width(2)
		context.move_to(img_x, img_y)
		context.line_to(img_max_x, img_y)
		context.line_to(img_max_x, img_max_y)
		context.line_to(img_x, img_max_y)
		context.line_to(img_x, img_y)
		context.set_source_rgba(*label_class.font_color)
		context.stroke()

	def get_label_size(self, surface, label_text, label_class):
		context = cairo.Context(surface)
		font_face = context.select_font_face(label_class.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		context.set_font_face(font_face)
		context.set_font_size(label_class.font_size)
		text_extents = context.text_extents(label_text)
		width, height = text_extents[2], text_extents[3]
		return (context, width, height, label_text)

	def build_image(self, surface, node):
		img_bytes = StringIO.StringIO()
		img_id = tiletree.build_node_id(node.zoom_level, node.tile_x, node.tile_y)
		surface.write_to_png(img_bytes)
		return (img_id, img_bytes)

	#returns (is_in_tile, bbox)
	def position_label(self, shape, node, img_w, img_h, label_spacing, label_width, label_height):
		if(self.point_labels):
			return self.position_point_label(shape, node, img_w, img_h, label_spacing, label_width, label_height)
		return self.position_poly_label(shape, node, img_w, img_h, label_spacing, label_width, label_height)

	def position_point_label(self, shape, node, img_w, img_h, label_spacing, label_width, label_height):
		seed_point = shape.getCentroid()

		x_scale = (node.max_x - node.min_x) / float(img_w)
		y_scale = (node.max_y - node.min_y) / float(img_h)
		label_geo_w = label_width * x_scale * .5
		label_geo_h = label_height * y_scale * .5

		#put the text to the right of the point
		label_geo_bbox = (seed_point.x + (self.point_buffer * x_scale), seed_point.y - label_geo_h,
				seed_point.x + label_geo_w * 2, seed_point.y + label_geo_h) 

		is_in_tile = False
		if(bbox_check(label_geo_bbox, (node.min_x, node.min_y, node.max_x, node.max_y))):
			is_in_tile = True

		return (is_in_tile, label_geo_bbox)

	def find_poly_label_ghost(self, seed_x, seed_y, node, x_repeat_interval, y_repeat_interval):
		x_mid = (node.max_x + node.min_x) / 2.0
		y_mid = (node.max_y + node.min_y) / 2.0
		x_spaces = math.floor((x_mid - seed_x)/float(x_repeat_interval) + .5)
		y_spaces = math.floor((y_mid - seed_y)/float(y_repeat_interval) + .5)

		ghost_x = seed_x + x_spaces * x_repeat_interval
		ghost_y = seed_y + y_spaces * y_repeat_interval

		return ghost_x, ghost_y

	def build_label_line(self, y_pos, min_x, max_x):
		wkt = 'MULTILINESTRING((%(min_x)s %(y_pos)s, %(max_x)s %(y_pos)s))'
		return mapscript.shapeObj.fromWKT(wkt % {'min_x':min_x, 'max_x':max_x, 'y_pos':y_pos})

	def position_poly_label(self, shape, node, img_w, img_h, label_spacing, label_width, label_height):
		x_scale = (node.max_x - node.min_x) / float(img_w)
		y_scale = (node.max_y - node.min_y) / float(img_h)
		label_geo_w = label_width * x_scale * .5
		label_geo_h = label_height * y_scale * .5
		x_repeat_interval = label_spacing * x_scale
		y_repeat_interval = label_spacing * y_scale

		#this crashes :(
		#shape = shape.simplify(min(x_scale, y_scale))

		tile_shape = mapscript.rectObj(node.min_x, node.min_y, node.max_x, node.max_y).toPolygon()
		if(shape.contains(tile_shape)):
			node.is_full = True

		seed_point = shape.getCentroid()
		ghost_x, ghost_y  = self.find_poly_label_ghost(seed_point.x, seed_point.y, node,
				x_repeat_interval,  y_repeat_interval)
		min_label_x = ghost_x - (x_scale * self.label_adjustment_max)
		max_label_x = ghost_x + (x_scale * self.label_adjustment_max)

		y_pos = ghost_y
		good_position = False
		position_interval = min(shape.bounds.maxy, ghost_y + self.label_adjustment_max) -\
			max(shape.bounds.miny, ghost_y - self.label_adjustment_max)
		position_interval /= float(self.position_attempts)
		#keep trying y positions until we find one that works
		for attempt_iter in range(self.position_attempts):
			#for this  y position, use a horizontal line to 
			#try and position the label

			label_line = self.build_label_line(y_pos, min_label_x, max_label_x)
			label_line = label_line.intersection(shape)

			if(not label_line):
				continue

			for line_iter in range(label_line.numlines):
				line = label_line.get(line_iter)
				if(line.numpoints != 2):
					continue
				min_x = min(line.get(0).x, line.get(1).x)
				max_x = max(line.get(0).x, line.get(1).x)
				if((max_x - min_x) >= (label_geo_w * 2)):
					ghost_x = (max_x + min_x) / 2.0
					ghost_y = y_pos
					good_position = True
					break

			if(good_position):
				break

			#calculate the next y position to try
			if(attempt_iter % 2 == 0):
				y_pos = ghost_y - (position_interval * attempt_iter / 2)
			else:
				y_pos = ghost_y + (position_interval * attempt_iter / 2)

		if(not good_position):
			return None

		label_geo_bbox = (ghost_x - label_geo_w, ghost_y - label_geo_h,
				ghost_x + label_geo_w, ghost_y + label_geo_h) 

		is_in_tile = False
		if(bbox_check(label_geo_bbox, (node.min_x, node.min_y, node.max_x, node.max_y))):
			is_in_tile = True

		return (is_in_tile, label_geo_bbox)

	def collision_check(self, node, check_bbox, label_bboxes):
		for l in label_bboxes:
			if(bbox_check(l, check_bbox)):
				return True
		return False

	def render_pos_results(self, node, context, label_bboxes, label_class, label_text, is_in_tile, label_extent):
		color = (1, 0, 0, 1)
		if(self.collision_check(node, label_extent, label_bboxes)):
			color = (0, 1, 0, 1)
			return

		label_bboxes.append(label_extent)
		if(not is_in_tile):
			return

		img_x, img_y = tiletree.geo_coord_to_img(label_extent[0], label_extent[1],
				self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)
		img_max_x, img_max_y = tiletree.geo_coord_to_img(label_extent[2], label_extent[3],
				self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)

		#TODO: add fontconfig with zoom level range and other options
		label_class.font_color = color
		self.render_label(context, label_text, img_x, img_y, img_max_x, img_max_y, label_class)

	#return (is_empty, is_leaf)
	def render_class(self, node, scale_denom, layer, surface, label_class, label_bboxes):
		#check for the scale
		if(node.zoom_level > label_class.max_zoom):
			return (True, True)
		if(node.zoom_level < label_class.min_zoom):
			return (True, False)
		if(label_class.mapserver_query == None):
			label_class.mapserver_query = "(1 == 1)"

		is_empty = True
		is_leaf = True

		layer.queryByAttributes(self.mapfile, '', label_class.mapserver_query, mapscript.MS_MULTIPLE)
		layer.open()
		num_results = layer.getNumResults()
		for f in range(num_results):
			result = layer.getResult(f)
			shape = layer.getShape(result)
			label_text = unicode(shape.getValue(self.label_col_index), 'latin_1')
			context, label_width, label_height, label_text =\
				self.get_label_size(surface, label_text, label_class)

			#weed out some false positives
			if(not self.mapfile.extent.toPolygon().intersects(shape)):
				continue

			is_empty = False
			is_leaf = False

			#if(label_text != 'Stafford'):
				#continue

			pos_results = self.position_label(shape, node, self.img_w, self.img_h, self.label_spacing,
					label_width, label_height)

			if(node.is_full):
				node.metadata = json.dumps({
					'label_text': label_text,
					'seed_point': [shape.getCentroid().x, shape.getCentroid().y],
					'layer_name': layer.name
				})

			if(pos_results == None):
				continue

			self.render_pos_results(node, context, label_bboxes, label_class, label_text,
					pos_results[0], pos_results[1])

		layer.close()

		self.mapfile.freeQuery()

		return (is_empty, is_leaf)

	def render(self, node):
		if(not self.point_labels and node.is_full):
			return self.render_full_poly(node)
		return self.render_normal(node)

	def render_full_poly(self, node):
		node.is_full = True
		node.is_empty = True
		if(node.zoom_level > self.max_zoom):
			node.is_leaf = True

		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.img_w, self.img_h)
		metadata = json.loads(node.metadata)
		label_text = metadata['label_text']
		seed_point_x, seed_point_y = metadata['seed_point']
		x_scale = (node.max_x - node.min_x) / float(self.img_w)
		y_scale = (node.max_y - node.min_y) / float(self.img_h)
		x_repeat_interval = self.label_spacing * x_scale
		y_repeat_interval = self.label_spacing * y_scale

		for label_class in self.label_classes[metadata['layer_name']]:
			if(node.zoom_level > label_class.max_zoom):
				continue
			if(node.zoom_level < label_class.min_zoom):
				continue

			context, label_width, label_height, label_text = self.get_label_size(surface, label_text, label_class)
			label_geo_w = label_width * x_scale * .5
			label_geo_h = label_height * y_scale * .5
			ghost_x, ghost_y = self.find_poly_label_ghost(seed_point_x, seed_point_y, node, x_repeat_interval,
				y_repeat_interval)
			label_geo_bbox = (ghost_x - label_geo_w, ghost_y - label_geo_h,
					ghost_x + label_geo_w, ghost_y + label_geo_h) 

			is_in_tile = False
			if(bbox_check(label_geo_bbox, (node.min_x, node.min_y, node.max_x, node.max_y))):
				is_in_tile = True

			#TODO: label_bboxes here!
			self.render_pos_results(node, context, [], label_class, label_text, is_in_tile, label_geo_bbox)

		return self.build_image(surface, node)


	def render_normal(self, node):
		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.img_w, self.img_h)
		#convert from a pixel buffer distance to an image buffer distance
		x_scale = (node.max_x - node.min_x) / float(self.img_w) 
		y_scale = (node.max_y - node.min_y) / float(self.img_h)
		x_buffer = x_scale * self.tile_buffer
		y_buffer = y_scale * self.tile_buffer

		label_bboxes = []

		#hack to get the correct scale
		self.mapfile.setExtent(node.min_x , node.min_y, node.max_x, node.max_y)
		scale_denom = self.mapfile.scaledenom
		if(self.point_labels):
			self.mapfile.setExtent(node.min_x - x_buffer, node.min_y - y_buffer,
					node.max_x + x_buffer, node.max_y + y_buffer)

		node.is_empty = True
		is_leaf = True

		for layer_name in self.mapserver_layers:
			layer = self.mapfile.getLayerByName(layer_name)
			for label_class in self.label_classes[layer_name]:
				this_empty, this_leaf = \
						self.render_class(node, scale_denom, layer, surface, label_class, label_bboxes)

				if(not this_empty):
					node.is_empty = False
				if(not this_leaf):
					is_leaf = False

		if(not node.is_full):
			if(node.is_empty and is_leaf):
				node.is_leaf = True

		return self.build_image(surface, node)

