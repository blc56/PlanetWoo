##\file pil.py render classes for the tiletree module. 
from tiletree import *
import shapely
import shapely.wkt
import shapely.geometry
import Image
import ImageDraw
import StringIO
import numpy

def renderPILRing(image_draw, ring, draw_options, coord_translate_func):
	coords = numpy.array(ring.xy)
	image_draw.polygon([coord_translate_func(x) for x in coords], **draw_options)

def renderPILPolygon(image_draw, polygon, outer_ring_options, inner_ring_options, coord_translate_func):
	renderPILRing(image_draw, polygon.exterior, outer_ring_options, coord_translate_func)
	for ring in polygon.interiors:
		renderPILRing(image_draw, ring, inner_ring_options, coord_translate_func)

def renderShape(image_draw, shape, outer_ring_options, inner_ring_options, coord_translate_func):
	if(hasattr(shape, 'geoms')):
		renderCollection(image_draw, shape, outer_ring_options, inner_ring_options, coord_translate_func)
	elif(shape.geom_type == 'Polygon'):
		renderPILPolygon(image_draw, shape, outer_ring_options, inner_ring_options, coord_translate_func)
	else:
		raise Exception('Unknown shape type! %s' % repr(shape.geom_type) )

def renderCollection(image_draw, collection, outer_ring_options, inner_ring_options, coord_translate_func):
	for shape in collection:
		renderShape(image_draw, shape, outer_ring_options, inner_ring_options, coord_translate_func)

class PILRenderer(Renderer):
	def __init__(self, img_w=256, img_h=256, img_prefix='images/', fill=(255, 0, 0, 255), outline=(0, 255, 0, 255)):
		Renderer.__init__(self, img_w, img_h, img_prefix)
		self.outer_ring_options = {
			'fill': '#FF0000',
			#'outline': outline
		}
		self. inner_ring_options = {
			'fill': '#00FF00',
		}

	def render_normal(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level, tile_x, tile_y):
		image = Image.new("RGB", (self.img_w, self.img_h))
		drawing = ImageDraw.Draw(image)

		try:
			x_scale = self.img_w / float(max_x - min_x)
			y_scale = self.img_h / float(max_y - min_y)
		except ZeroDivisionError:
			x_scale = 1
			y_scale = 1

		#if(geometry):
			#geometry = geometry.simplify(1/x_scale, preserve_topology=True)

		translate_coord = lambda x : ( (x[0] - min_x) * x_scale, (max_y - x[1]) * y_scale )

		renderShape(drawing, geometry, self.outer_ring_options, self.inner_ring_options, translate_coord)

		result = StringIO.StringIO()
		image.save(result, 'png')
		img_id = build_node_id(zoom_level, tile_x, tile_y)

		return (img_id, result)

