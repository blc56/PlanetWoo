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
	def __init__(self, font='arial', font_size=12, mapserver_query="(1==1)", font_color_fg=(0, 0, 0, 1),
			font_color_bg=None, min_zoom=0, max_zoom=19, weight="normal"):
		self.font = font
		self.font_size = font_size
		self.mapserver_query = mapserver_query
		self.font_color_fg = font_color_fg
		self.font_color_bg = font_color_bg
		self.min_zoom = min_zoom
		self.max_zoom = max_zoom
		self.weight = weight

	def to_dict(self):
		return copy.copy(self.__dict__)

	def from_dict(self, in_dict):
		self.__dict__.update(in_dict)

class LabelRenderer:
	def __init__(self, mapfile_string, label_col_index, mapserver_layers,
			min_zoom=0, max_zoom=100, label_spacing=1024, img_w=256, img_h=256, tile_buffer=256,
			point_labels=False, point_buffer=4, position_attempts=4, label_buffer=0):
		self.mapfile = mapscript.fromstring(mapfile_string)
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
		self.label_buffer = label_buffer
		self.position_attempts = position_attempts
		self.label_adjustment_max = (self.label_spacing / 2.0) - max(self.img_w, self.img_h)
		if(self.label_adjustment_max < 0):
			raise Exception("Bad parameters")
		self.label_classes = {}
		self.blank_img_bytes = None

	def add_label_class(self, layer_name, label_class):
		layer_classes = self.label_classes.setdefault(layer_name, [])
		layer_classes.append(label_class)

	def tile_info(self, node, check_full=True):
		node.is_blank = False
		node.is_leaf = False
		node.is_full = False

		if(node.zoom_level < self.min_zoom):
			#we know this is going to be a blank node
			node.is_blank = True

			x_scale = (node.max_x - node.min_x) / float(self.img_w) 
			y_scale = (node.max_y - node.min_y) / float(self.img_h)
			x_buffer = x_scale * self.tile_buffer
			y_buffer = y_scale * self.tile_buffer

			#check if this is going to be a leaf node
			if(self.point_labels):
				rect = mapscript.rectObj(node.min_x - x_buffer, node.min_y - y_buffer,
							node.max_x + x_buffer, node.max_y + y_buffer)
			else:
				rect = mapscript.rectObj(node.min_x, node.min_y,
							node.max_x, node.max_y)

			self.mapfile.queryByRect(rect)

			#check if this is going to be a leaf node
			node.is_leaf = True
			for layer_name in self.mapserver_layers:
				layer = self.mapfile.getLayerByName(layer_name)
				layer.open()
				num_results = layer.getNumResults()
				layer.close()
				if(num_results > 0):
					node.is_leaf = False
					return

		if(node.zoom_level > self.max_zoom):
			node.is_blank = True
			node.is_full = True

	def draw_text(self, img_x, img_y, text, context):
		context.move_to(img_x, img_y)
		context.text_path(text)

	def shadow_text(self, x, y, text, context, buffer_radius=2, radius_step = 1, n_sections=10):
		radius = radius_step
		while(radius < buffer_radius+radius_step):
			f_radius = float(radius)
			for s in range(n_sections):
				rads = (2.0 * math.pi) * (s / float(n_sections))
				x_shift,y_shift = math.cos(rads)*f_radius,math.sin(rads)*f_radius
				self.draw_text(x+x_shift,y+y_shift,text, context)
			radius += radius_step

	def render_label(self, context, label_text, img_x, img_y, img_max_x, img_max_y, label_class):
		if(label_class.font_color_bg != None):
			context.set_source_rgba(*label_class.font_color_bg)
			self.shadow_text(img_x, img_y, label_text, context)
			context.fill()
		context.set_source_rgba(*label_class.font_color_fg)
		self.draw_text(img_x, img_y, label_text, context)
		context.fill()

		#context.move_to(img_x, img_y)
		#context.line_to(img_max_x, img_y)
		#context.line_to(img_max_x, img_max_y)
		#context.line_to(img_x, img_max_y)
		#context.line_to(img_x, img_y)
		#context.set_source_rgba(1, 0, 0, 1)
		#context.stroke()

	def get_label_size(self, surface, label_text, label_class):
		context = cairo.Context(surface)
		weight = cairo.FONT_WEIGHT_NORMAL
		if(label_class.weight == "bold"):
			weight = cairo.FONT_WEIGHT_BOLD
		font_face = context.select_font_face(label_class.font, cairo.FONT_SLANT_NORMAL, )
		context.set_font_face(font_face)
		context.set_font_size(label_class.font_size)
		text_extents = context.text_extents(label_text)
		width, height = text_extents[4] + text_extents[0], text_extents[3]
		return (context, width, height, label_text)

	def build_image(self, surface, node):
		img_bytes = StringIO.StringIO()
		img_id = tiletree.build_node_id(node.zoom_level, node.tile_x, node.tile_y)
		surface.write_to_png(img_bytes)
		return (img_id, img_bytes)

	#returns (is_in_tile, bbox)
	def position_label(self, shape, node, label_width, label_height):
		if(self.point_labels):
			return self.position_point_label(shape, node, label_width, label_height)
		return self.position_poly_label(shape, node, label_width, label_height)

	def position_point_label(self, shape, node, label_width, label_height):
		seed_point = shape.getCentroid()

		x_scale = (node.max_x - node.min_x) / float(self.img_w)
		y_scale = (node.max_y - node.min_y) / float(self.img_h)
		label_geo_w = label_width * x_scale * .5
		label_geo_h = label_height * y_scale * .5

		#put the text to the right of the point
		x_buffer = self.label_buffer * x_scale
		y_buffer = self.label_buffer * y_scale
		#x_buffer = 0
		#y_buffer = 0
		label_geo_bbox = (seed_point.x + (self.point_buffer * x_scale), seed_point.y - label_geo_h,
				seed_point.x + (label_geo_w * 2) + x_buffer, seed_point.y + label_geo_h + y_buffer) 

		#make sure that this label doesnt intersect with any other labels
		label_shape = mapscript.rectObj(*label_geo_bbox).toPolygon()
		if(node.label_geoms != None):
			if(label_shape.intersects(node.label_geoms)):
				return None
			node.label_geoms =label_shape.Union(node.label_geoms)
		else:
			node.label_geoms = label_shape

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

	def position_poly_label(self, shape, node, label_width, label_height):
		x_scale = (node.max_x - node.min_x) / float(self.img_w)
		y_scale = (node.max_y - node.min_y) / float(self.img_h)
		label_geo_w = label_width * x_scale * .5
		label_geo_h = label_height * y_scale * .5
		x_repeat_interval = self.label_spacing * x_scale
		y_repeat_interval = self.label_spacing * y_scale
		x_buffer = self.label_buffer * x_scale
		y_buffer = self.label_buffer * y_scale

		#this crashes :(
		#shape = shape.simplify(min(x_scale, y_scale))

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
			#make sure the label is contained by its corresponding geometry
			label_line = label_line.intersection(shape)
			if(not label_line):
				continue
			#make sure the label doesn't collided with any other labels
			if(node.label_geoms != None):
				label_line = label_line.difference(node.label_geoms)
			if(not label_line):
				continue

			for line_iter in range(label_line.numlines):
				line = label_line.get(line_iter)
				if(line.numpoints != 2):
					continue
				min_x = min(line.get(0).x, line.get(1).x)
				max_x = max(line.get(0).x, line.get(1).x)
				if((max_x - min_x) >= (label_geo_w * 2)):
					#do a final check that considers the height of the label
					x_pos = (max_x + min_x) / 2.0
					label_geo_bbox = (x_pos - label_geo_w, y_pos - label_geo_h,
							x_pos + label_geo_w + x_buffer, y_pos + label_geo_h + y_buffer) 
					label_shape = mapscript.rectObj(*label_geo_bbox).toPolygon()
					if(node.label_geoms != None):
						if(label_shape.intersects(node.label_geoms)):
							continue
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

		if(node.label_geoms != None):
			node.label_geoms =label_shape.Union(node.label_geoms)
		else:
			node.label_geoms = label_shape

		is_in_tile = False
		if(bbox_check(label_geo_bbox, (node.min_x, node.min_y, node.max_x, node.max_y))):
			is_in_tile = True

		return (is_in_tile, label_geo_bbox)

	def render_pos_results(self, node, context, label_class, label_text, is_in_tile, label_extent):
		if(not is_in_tile):
			return

		img_x, img_y = tiletree.geo_coord_to_img(label_extent[0], label_extent[1],
				self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)
		img_max_x, img_max_y = tiletree.geo_coord_to_img(label_extent[2], label_extent[3],
				self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)

		self.render_label(context, label_text, img_x, img_y, img_max_x, img_max_y, label_class)

	#return (is_blank, is_leaf)
	def render_class(self, node, scale_denom, layer, surface, label_class):
		#check for the scale
		if(node.zoom_level > label_class.max_zoom):
			return (True, True)
		if(node.zoom_level < label_class.min_zoom):
			#we know we aren't going to render this label class, but check to see if
			#this node would contain any features
			layer.queryByAttributes(self.mapfile, '', label_class.mapserver_query, mapscript.MS_SINGLE)
			layer.open()
			num_results = layer.getNumResults()
			layer.close()
			if(num_results > 0):
				return (True, False)
			return (True, True)

		if(label_class.mapserver_query == None):
			label_class.mapserver_query = "(1 == 1)"

		is_blank = True
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

			is_blank = False
			is_leaf = False

			pos_results = self.position_label(shape, node, label_width, label_height)

			if(pos_results == None):
				continue

			self.render_pos_results(node, context, label_class, label_text, pos_results[0], pos_results[1])

		layer.close()

		self.mapfile.freeQuery()

		return (is_blank, is_leaf)

	def render_blank(self):
		if(self.blank_img_bytes == None):
			surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.img_w, self.img_h)
			self.blank_img_bytes = self.build_image(surface, node)[1]
		return (0, self.blank_img_bytes)

	def render(self, node):
		if(node.is_blank):
			return self.render_blank(self)

		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.img_w, self.img_h)

		#convert from a pixel buffer distance to an image buffer distance
		x_scale = (node.max_x - node.min_x) / float(self.img_w) 
		y_scale = (node.max_y - node.min_y) / float(self.img_h)
		x_buffer = x_scale * self.tile_buffer
		y_buffer = y_scale * self.tile_buffer

		#hack to get the correct scale
		self.mapfile.setExtent(node.min_x , node.min_y, node.max_x, node.max_y)
		scale_denom = self.mapfile.scaledenom
		if(self.point_labels):
			self.mapfile.setExtent(node.min_x - x_buffer, node.min_y - y_buffer,
					node.max_x + x_buffer, node.max_y + y_buffer)

		node.is_blank = True
		node.is_leaf = True
		node.is_full = False

		for layer_name in self.mapserver_layers:
			layer = self.mapfile.getLayerByName(layer_name)
			for label_class in self.label_classes[layer_name]:
				this_blank, this_leaf = \
						self.render_class(node, scale_denom, layer, surface, label_class) 
				if(not this_blank):
					node.is_blank = False
				if(not this_leaf):
					node.is_leaf = False

		return self.build_image(surface, node)

