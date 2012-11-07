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

##\file boundary_label.py Main classes for the tiletree.boundary_label module. 

import mapscript
import math

import planetwoo.tiletree as tiletree
import planetwoo.tiletree.label as label

def calc_distance(x1, y1, x2, y2):
	return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def calc_cos(x1, y1, x2, y2):
	if((x1 + y1) == 0 or (x2 + y2) == 0):
		return 1
	return (x1*x2 + y1*y2) / math.sqrt( (x1**2 + y1**2) * (x2**2 + y2**2) )

class BoundaryLabelRenderer(label.BaseLabelRenderer):
	def __init__(self, mapfile_string, label_col_index, mapserver_layers,
			min_zoom=0, max_zoom=100, label_spacing=1024, img_w=256, img_h=256, tile_buffer=256,
			info_cache_name=None, cos_tolerance=.985):
		label.BaseLabelRenderer.__init__(self, mapfile_string, label_col_index, mapserver_layers,
			min_zoom=min_zoom, max_zoom=max_zoom, label_spacing=label_spacing, img_w=img_w, img_h=img_h,
			tile_buffer=256, info_cache_name=info_cache_name)

		#self.label_spacing_sq = self.label_spacing**2
		self.cos_tolerance = cos_tolerance

	def tile_info(self, node, check_full=True):
		node.is_blank = False
		node.is_leaf = False
		node.is_full = False

	def cos_test(self, line, node, point_index, label_width):
		label_width = label_width / 2


		#check to make sure that we aren't trying to draw the label on an extreme bend 
		#iterate through label_width/2 worth of points to each side of the label point
		#and see if the normals fall into a tolerance

		#get a base vector to compare all of the other vectors to
		base_point1 = line.get(point_index)
		base_x1, base_y1 = tiletree.geo_coord_to_img(base_point1.x, base_point1.y,
				self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)
		base_point2 = line.get( (point_index + 1) % line.numpoints)
		base_x2, base_y2 = tiletree.geo_coord_to_img(base_point2.x, base_point2.y,
				self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)

		base_x, base_y = (base_x2 - base_x1, base_y2 - base_y1)

		min_cos = 1
		point_iter = point_index
		distance = 0
		last_x, last_y = base_x1, base_y1
		while(distance < label_width):
			point_iter += 1
			point_iter %= line.numpoints
			this_point = line.get(point_iter)
			this_x, this_y = tiletree.geo_coord_to_img(this_point.x, this_point.y,
					self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)
			distance += calc_distance(this_x, this_y, last_x, last_y)
			cos = abs(calc_cos(this_x - last_x, this_y - last_y, base_x, base_y))
			#if(cos < self.cos_tolerance):
				#return False, cos
			min_cos = min(min_cos, cos)
			last_x, last_y = this_x, this_y

		point_iter = point_index
		distance = 0
		last_x, last_y = base_x1, base_y1
		while(distance < label_width):
			point_iter -= 1
			point_iter %= line.numpoints
			this_point = line.get(point_iter)
			this_x, this_y = tiletree.geo_coord_to_img(this_point.x, this_point.y,
					self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)
			distance += calc_distance(this_x, this_y, last_x, last_y)
			cos = abs(calc_cos(this_x - last_x, this_y - last_y, base_x, base_y))
			#if(cos < self.cos_tolerance):
				#return False, cos
			min_cos = min(min_cos, cos)
			last_x, last_y = this_x, this_y

		#return True, 'T'
		return min_cos


	def position_poly_label(self, shape, node, node_extent_shape, label_width, label_height, context, label_text):
		x_scale = (node.max_x - node.min_x) / float(self.img_w)
		y_scale = (node.max_y - node.min_y) / float(self.img_h)
		x_scale_inv = 1 / x_scale
		y_scale_inv = 1 / y_scale

		#TODO: some kind of caching algorithm (memcached backend?) so 
		#we don't have to do this operation a whole bunch!!!
		scale = max(x_scale, y_scale)
		shape = shape.buffer(-(scale*label_height))

		if(not shape):
			return None

		distance_since_last_label = 0
		import math
		line = shape.get(0)
		for line_iter in range(shape.numlines):
			line = shape.get(line_iter)

			if(line.numpoints == 0):
				continue

			first_point = line.get(0)
			last_x, last_y = tiletree.geo_coord_to_img(first_point.x, first_point.y,
					self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)
			for point_iter in range(1, line.numpoints):
				point = line.get(point_iter)
				this_x, this_y = tiletree.geo_coord_to_img(point.x, point.y,
					self.img_w, self.img_h, node.min_x, node.min_y, node.max_x, node.max_y)
				distance_since_last_label += calc_distance(this_x, this_y, last_x, last_y)

				if(distance_since_last_label > self.label_spacing ):
					#do fancy stuff
					distance_since_last_label = 0
					if(node_extent_shape.contains(point)):
						debug =  self.cos_test(line, node, point_iter, label_width)
						#context.set_source_rgba(*label_class.font_color_bg)
						context.set_source_rgba(1, 0, 0, 1)
						context.move_to(this_x, this_y)
						#context.text_path(unicode(max_cos) + ' , ' + unicode(min_cos))
						context.text_path(unicode(debug))
						context.fill()

				last_x = this_x
				last_y = this_y


	def render_class(self, node, layer, surface, label_class):
		zoom_check = self.render_class_zoom_check(node, layer, label_class)
		if(zoom_check != None):
			return zoom_check

		if(label_class.mapserver_query == None):
			label_class.mapserver_query = "(1 == 1)"

		is_blank = True
		is_leaf = True

		layer.queryByAttributes(self.mapfile, '', label_class.mapserver_query, mapscript.MS_MULTIPLE)
		layer.open()
		num_results = layer.getNumResults()
		node_extent_shape = self.mapfile.extent.toPolygon()
		for f in range(num_results):
			result = layer.getResult(f)
			shape = layer.getShape(result)
			label_text = unicode(shape.getValue(self.label_col_index), 'latin_1')

			if(not label_text):
				continue

			#weed out some false positives
			if(not node_extent_shape.intersects(shape)):
				continue

			context, label_width, label_height, label_text =\
				self.get_label_size(surface, label_text, label_class)

			#TODO: magic drawing code!!!
			self.position_poly_label(shape, node, node_extent_shape, label_width, label_height, context, label_text)

			is_blank = False
			is_leaf = False

		layer.close()

		self.mapfile.freeQuery()

		return (is_blank, is_leaf)


