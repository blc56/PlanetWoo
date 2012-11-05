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

##\file label.py Main classes for the tiletree.label module. 
import StringIO
import mapscript
import cairo
import math
import sys
import shapely
import json
import copy

import planetwoo.tiletree as tiletree

ALMOST_ZERO = float(1e-10)

import ctypes
import cairo

#shameless copy and paste from http://cairographics.org/freetypepython/
CAIRO_STATUS_SUCCESS = 0
FT_Err_Ok = 0

# find shared objects
_freetype_so = ctypes.CDLL ("libfreetype.so.6")
_cairo_so = ctypes.CDLL ("libcairo.so.2")

_cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ctypes.c_void_p
_cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [ ctypes.c_void_p, ctypes.c_int ]
_cairo_so.cairo_set_font_face.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
_cairo_so.cairo_font_face_status.argtypes = [ ctypes.c_void_p ]
_cairo_so.cairo_status.argtypes = [ ctypes.c_void_p ]

# initialize freetype
_ft_lib = ctypes.c_void_p ()
if FT_Err_Ok != _freetype_so.FT_Init_FreeType (ctypes.byref (_ft_lib)):
  raise "Error initialising FreeType library."

class PycairoContext(ctypes.Structure):
	_fields_ = [("PyObject_HEAD", ctypes.c_byte * object.__basicsize__),
		("ctx", ctypes.c_void_p),
		("base", ctypes.c_void_p)]

_surface = cairo.ImageSurface (cairo.FORMAT_A8, 0, 0)

def create_cairo_font_face_for_file (filename, faceindex=0, loadoptions=0):
	global _freetype_so
	global _cairo_so
	global _ft_lib
	global _surface

	filename = str(filename)

	# create freetype face
	ft_face = ctypes.c_void_p()
	cairo_ctx = cairo.Context (_surface)
	cairo_t = PycairoContext.from_address(id(cairo_ctx)).ctx

	if FT_Err_Ok != _freetype_so.FT_New_Face (_ft_lib, filename, faceindex, ctypes.byref(ft_face)):
		raise Exception("Error creating FreeType font face for " + filename)

	# create cairo font face for freetype face
	cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face (ft_face, loadoptions)
	if CAIRO_STATUS_SUCCESS != _cairo_so.cairo_font_face_status (cr_face):
		raise Exception("Error creating cairo font face for " + filename)

	_cairo_so.cairo_set_font_face (cairo_t, cr_face)
	if CAIRO_STATUS_SUCCESS != _cairo_so.cairo_status (cairo_t):
		raise Exception("Error creating cairo font face for " + filename)

	face = cairo_ctx.get_font_face ()

	return face

#end shameless copy/paste

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

class BaseLabelRenderer(tiletree.Renderer):
	def __init__(self, mapfile_string, label_col_index, mapserver_layers,
			min_zoom=0, max_zoom=100, label_spacing=1024, img_w=256, img_h=256, tile_buffer=256,
			info_cache_name=None):
		tiletree.Renderer.__init__(self, img_w, img_h, info_cache_name)
		self.mapfile = mapscript.fromstring(mapfile_string)
		self.label_col_index = label_col_index
		self.mapserver_layers = mapserver_layers
		self.label_spacing = label_spacing
		self.img_w = img_w
		self.img_h = img_h
		self.tile_buffer = tile_buffer
		self.min_zoom = min_zoom
		self.max_zoom = max_zoom
		self.label_classes = {}
		self.blank_img_bytes = None
		self.font_faces = {}

	def get_font_face(self, ttf_file):
		if(ttf_file in self.font_faces):
			return self.font_faces[ttf_file]
		self.font_faces[ttf_file] = create_cairo_font_face_for_file(ttf_file, 0)
		return self.font_faces[ttf_file]

	def add_label_class(self, layer_name, label_class):
		layer_classes = self.label_classes.setdefault(layer_name, [])
		layer_classes.append(label_class)

class LabelRenderer(BaseLabelRenderer):
	def __init__(self, mapfile_string, label_col_index, mapserver_layers,
			min_zoom=0, max_zoom=100, label_spacing=1024, img_w=256, img_h=256, tile_buffer=256,
			point_labels=False, point_buffer=4, position_attempts=4, label_buffer=0,
			info_cache_name=None):
		BaseLabelRenderer.__init__(self, mapfile_string, label_col_index, mapserver_layers,
			min_zoom=min_zoom, max_zoom=max_zoom, label_spacing=label_spacing, img_w=img_w, img_h=img_h,
			tile_buffer=256, info_cache_name=info_cache_name)
		self.point_labels = point_labels
		self.point_buffer = point_buffer
		self.label_buffer = label_buffer
		self.position_attempts = position_attempts
		self.label_adjustment_max = (self.label_spacing / 2.0) - max(self.img_w, self.img_h)
		if(self.label_adjustment_max < 0):
			raise Exception("Bad parameters")

	def tile_info(self, node, check_full=True):
		node.is_blank = False
		node.is_leaf = False
		node.is_full = False

		#when we call render() tile info will be computed
		#go ahead an compute it if this node is not in a zoom level
		#where this tile would be rendered
		if(node.zoom_level < self.min_zoom):
			#we know this is going to be a blank node
			node.is_blank = True
			return

			#x_scale = (node.max_x - node.min_x) / float(self.img_w) 
			#y_scale = (node.max_y - node.min_y) / float(self.img_h)
			#x_buffer = x_scale * self.tile_buffer
			#y_buffer = y_scale * self.tile_buffer

			#rect = mapscript.rectObj(node.min_x - x_buffer, node.min_y - y_buffer,
						#node.max_x + x_buffer, node.max_y + y_buffer)

			#self.mapfile.queryByRect(rect)

			##check if this is going to be a leaf node
			#node.is_leaf = True
			#for layer_name in self.mapserver_layers:
				#layer = self.mapfile.getLayerByName(layer_name)
				#layer.open()
				#num_results = layer.getNumResults()
				#if(num_results > 0):
					#node.is_leaf = False
					#return
				#if(check_full and num_results == 1):
					#result = layer.getResult(0)
					#shape = layer.getShape(result)
					#bbox_shape = mapscript.extent.toPolygon()
					#if(shape.contains(bbox_shape)):
						#node.is_full=True
				#layer.close()

		if(node.zoom_level > self.max_zoom):
			node.is_blank = True
			node.is_leaf = True

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
		x_pos = img_x
		y_pos = img_y
		lines = label_text.splitlines()
		lines.reverse()
		y_inc = (img_max_y - img_y) / float(len(lines))
		for line in lines:
			if(label_class.font_color_bg != None):
				context.set_source_rgba(*label_class.font_color_bg)
				self.shadow_text(x_pos, y_pos, line, context)
				context.fill()
			context.set_source_rgba(*label_class.font_color_fg)
			self.draw_text(x_pos, y_pos, line, context)
			context.fill()

			y_pos += y_inc

		#context.move_to(img_x, img_y)
		#context.line_to(img_max_x, img_y)
		#context.line_to(img_max_x, img_max_y)
		#context.line_to(img_x, img_max_y)
		#context.line_to(img_x, img_y)
		#context.set_source_rgba(1, 0, 0, 1)
		#context.stroke()

	def get_line_size(self, context, label_text):
		text_extents = context.text_extents(label_text)
		width, height = text_extents[4] + text_extents[0], text_extents[3]
		return width, height

	def split_label(self, context, label_text):
		label_text = label_text.strip()
		#find all spaces in the label
		start = 0
		# a list of (distance_from_center, pos)
		split_pos = []
		center = len(label_text) / 2
		#TODO: add regex support for 'split characters'
		#so users can configure characters to split on
		while(True):
			pos = label_text.find(' ', start)
			if(pos < 0):
				break
			split_pos.append((center - pos, pos))
			start = pos + 1

		#try splitting
		if(len(split_pos) == 0):
			#we failed
			return label_text

		#split on the split char closest to the center of the line
		split = split_pos[0][1]
		label_text = label_text[0:split] + '\n' + label_text[split:]
		new_label = ''
		for line in label_text.splitlines():
			this_width, this_height = self.get_line_size(context, line)

			#if this line was too big, attempt to recurse and split it again
			new_line = line
			if(this_width > self.tile_buffer):
				new_line = self.split_label(context, line)

			new_label += new_line.strip() + '\n'

		return new_label.strip()
			

	def get_label_size(self, surface, label_text, label_class):
		context = cairo.Context(surface)
		weight = cairo.FONT_WEIGHT_NORMAL
		#if(label_class.weight == "bold"):
			#weight = cairo.FONT_WEIGHT_BOLD
		#font_face = context.select_font_face(label_class.font, cairo.FONT_SLANT_NORMAL, )
		font_face = self.get_font_face(label_class.font)
		context.set_font_face(font_face)
		context.set_font_size(label_class.font_size)
		width, height = self.get_line_size(context, label_text)

		#if the label is too long, split it
		#and calculate the new label size
		if(width > self.tile_buffer):
			label_text = self.split_label(context, label_text)
			width = 0
			height = 0
			for line in label_text.splitlines():
				this_width, this_height = self.get_line_size(context, line)
				width = max(this_width, width)
				height += this_height

		return (context, width, height, label_text)

	def build_image(self, surface, node):
		img_bytes = StringIO.StringIO()
		img_id = tiletree.build_node_id(node.zoom_level, node.tile_x, node.tile_y)
		surface.write_to_png(img_bytes)
		img_bytes = tiletree.palette_png_bytes(StringIO.StringIO(img_bytes.getvalue()))
		return (img_id, img_bytes)

	#returns (is_in_tile, bbox)
	def position_label(self, shape, node, label_width, label_height):
		if(self.point_labels):
			return self.position_point_label(shape, node, label_width, label_height) 
		return self.position_poly_label(shape, node, label_width, label_height)

	def label_point_bbox(self, x, y, width, height, x_scale, y_scale, where_ud, where_lr):
		width = width * x_scale * .5
		height = height * y_scale * .5

		#TODO: add more options and user configurability here!

		if(where_ud == 'center'):
			min_y = y - height
			max_y = y + height + (self.label_buffer * y_scale)
		elif(where_ud == 'up'):
			min_y = y - height * 2 - (self.label_buffer * y_scale) - (self.point_buffer * y_scale)
			max_y = y  - (self.point_buffer * y_scale)
		elif(where_ud == 'down'):
			min_y = y + (self.point_buffer * y_scale)
			max_y = y + (self.point_buffer * y_scale) + (height*2) + (self.label_buffer * y_scale)

		if(where_lr == 'right'):
			min_x = x + (self.point_buffer * x_scale)
			max_x = x + (width * 2) + (self.label_buffer * x_scale)

		elif(where_lr == 'left'):
			max_x = x - (self.point_buffer * x_scale) + (self.label_buffer * x_scale)
			min_x = x - (self.point_buffer * x_scale) - width * 2

		return (min_x, min_y, max_x, max_y)

	def position_point_label(self, shape, node, label_width, label_height, where_ud='center', where_lr='right'):
		seed_point = shape.getCentroid()
		if(seed_point == None):
			return None

		x_scale = (node.max_x - node.min_x) / float(self.img_w)
		y_scale = (node.max_y - node.min_y) / float(self.img_h)

		#put the text to the right of the point
		label_geo_bbox = self.label_point_bbox(seed_point.x, seed_point.y, label_width, label_height,
				x_scale, y_scale, where_ud, where_lr)

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

	def fast_position_poly_label(self, shape, node, ghost_x, ghost_y, x_scale, y_scale, min_label_x, max_label_x, label_geo_w, label_geo_h):
		x_buffer = self.label_buffer * x_scale
		y_buffer = self.label_buffer * y_scale

		label_geo_bbox = (ghost_x - label_geo_w, ghost_y - label_geo_h,
				ghost_x + label_geo_w + x_buffer, ghost_y + label_geo_h + y_buffer) 

		label_shape = mapscript.rectObj(*label_geo_bbox).toPolygon()
		if(not shape.contains(label_shape)):
			return None

		if(node.label_geoms != None):
			if(label_shape.intersects(node.label_geoms)):
				return None

		return label_geo_bbox, label_shape

	def slow_position_poly_label(self, shape, node, ghost_x, ghost_y, x_scale, y_scale, min_label_x, max_label_x, label_geo_w, label_geo_h):
		x_buffer = self.label_buffer * x_scale
		y_buffer = self.label_buffer * y_scale

		y_pos = ghost_y
		good_position = False
		position_interval = min(shape.bounds.maxy, ghost_y + y_scale * self.label_adjustment_max) -\
			max(shape.bounds.miny, ghost_y - y_scale * self.label_adjustment_max)
		position_interval /= float(self.position_attempts)

		tile_shape = mapscript.rectObj(node.min_x, node.min_y, node.max_x, node.max_y).toPolygon()

		#keep trying y positions until we find one that works
		for attempt_iter in range(self.position_attempts):
			#for this  y position, use a horizontal line to 
			#try and position the label

			label_line = self.build_label_line(y_pos, min_label_x, max_label_x)
			#make sure the label is contained by its corresponding geometry
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
					#do a check that considers the height of the label
					x_pos = (max_x + min_x) / 2.0
					label_geo_bbox = (x_pos - label_geo_w, y_pos - label_geo_h,
							x_pos + label_geo_w + x_buffer, y_pos + label_geo_h + y_buffer) 
					label_shape = mapscript.rectObj(*label_geo_bbox).toPolygon()
					if(node.label_geoms != None):
						if(label_shape.intersects(node.label_geoms)):
							continue

					#don't let this label bleed into another tile if it has been
					#shifted
					#this avoids an infinite chain of label "corrections"
					if(attempt_iter !=0 and not tile_shape.contains(label_shape)):
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

		return label_geo_bbox, label_shape

	def position_poly_label(self, shape, node, label_width, label_height):
		x_scale = (node.max_x - node.min_x) / float(self.img_w)
		y_scale = (node.max_y - node.min_y) / float(self.img_h)
		label_geo_w = label_width * x_scale * .5
		label_geo_h = label_height * y_scale * .5
		x_repeat_interval = self.label_spacing * x_scale
		y_repeat_interval = self.label_spacing * y_scale

		#this crashes :(
		#shape = shape.simplify(min(x_scale, y_scale))

		seed_point = shape.getCentroid()
		if(seed_point == None):
			return None
		ghost_x, ghost_y = self.find_poly_label_ghost(seed_point.x, seed_point.y,
				node, x_repeat_interval,  y_repeat_interval)

		min_label_x = ghost_x - (x_scale * self.label_adjustment_max)
		max_label_x = ghost_x + (x_scale * self.label_adjustment_max)
		min_label_y = ghost_y - (y_scale * self.label_adjustment_max)
		max_label_y = ghost_y + (y_scale * self.label_adjustment_max)

		#if this label couldn't possibly intersect this tile + tile_buffer
		#then skip it!
		if(not bbox_check((min_label_x - label_geo_w, min_label_y - label_geo_h, 
				max_label_x + label_geo_w, max_label_y + label_geo_h),
				(self.mapfile.extent.minx, self.mapfile.extent.miny,
				self.mapfile.extent.maxx, self.mapfile.extent.maxy))):
			host_y = seed_y + y_spaces * y_repeat_interval
			return None

		pos_results = self.fast_position_poly_label(shape, node,
				ghost_x, ghost_y, x_scale, y_scale, min_label_x, max_label_x,
				label_geo_w, label_geo_h)
		#if the shape's area is less than 1/10 of a tile then don't bother 
		#trying to label it
		if(not pos_results and (shape.getArea() < (self.img_w * x_scale**2 * .1)) ):
			pos_results = self.slow_position_poly_label(shape, node,
					ghost_x, ghost_y, x_scale, y_scale, min_label_x, max_label_x,
					label_geo_w, label_geo_h)
		if(not pos_results):
			return None

		label_geo_bbox, label_shape = pos_results

		#update label_geoms
		if(node.label_geoms != None):
			node.label_geoms = label_shape.Union(node.label_geoms)
		else:
			node.label_geoms = label_shape

		#check if this label is in the tile
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

			if(not label_text):
				continue

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

	def render_blank(self, node):
		if(self.blank_img_bytes == None):
			surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.img_w, self.img_h)
			self.blank_img_bytes = self.build_image(surface, node)[1]
		return (0, self.blank_img_bytes)

	def render(self, node):

		if(node.is_blank):
			return self.render_blank(node)

		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.img_w, self.img_h)

		#convert from a pixel buffer distance to an image buffer distance
		x_scale = (node.max_x - node.min_x) / float(self.img_w) 
		y_scale = (node.max_y - node.min_y) / float(self.img_h)
		x_buffer = x_scale * self.tile_buffer
		y_buffer = y_scale * self.tile_buffer

		#hack to get the correct scale
		self.mapfile.setExtent(node.min_x , node.min_y, node.max_x, node.max_y)
		scale_denom = self.mapfile.scaledenom
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

