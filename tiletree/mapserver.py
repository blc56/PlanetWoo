##\file mapserver.py render classes for the tiletree module. 
from tiletree import *
import shapely
import shapely.wkt
import shapely.geometry
from psycopg2 import *
import time

class MapServerRenderer(NullRenderer):
	def __init__(self, mapfile_template, layers, img_w=256, img_h=256, img_prefix='images/'):
		NullRenderer.__init__(self, img_w, img_h, img_prefix)
		self.mapfile_template=mapfile_template
		self.layers=layers

		#creating a mapfile leaks memory, so only create it once
		template_args = {
			#'wkt': shapely.wkt.dumps(geometry),
			#'shapefile_path' : shapefile_path
		}
		self.mapfile = mapscript.fromstring(self.mapfile_template % template_args)

	def build_request(self, min_x, min_y, max_x, max_y):
		wms_req = mapscript.OWSRequest()
		wms_req.setParameter('MODE', 'WMS')
		wms_req.setParameter('VERSION', '1.1.1')
		wms_req.setParameter('FORMAT', 'image/png')
		wms_req.setParameter('TRANSPARENT', 'TRUE')
		wms_req.setParameter('WIDTH', str(self.img_w))
		wms_req.setParameter('HEIGHT', str(self.img_h))
		wms_req.setParameter('SRS', 'EPSG:3395')
		wms_req.setParameter('REQUEST', 'GetMap')
		wms_req.setParameter('BBOX', ','.join(str(x) for x in [min_x, min_y, max_x, max_y]))
		wms_req.setParameter('LAYERS', self.layers)

		return wms_req

	def render_normal(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		mapscript.msIO_installStdoutToBuffer()
		wms_req = self.build_request(min_x, min_y, max_x, max_y)

		self.mapfile.OWSDispatch(wms_req)

		mapscript.msIO_stripStdoutBufferContentType()

		img_id = self.next_img_id
		self.next_img_id += 1

		result =  (img_id,
				StringIO.StringIO(mapscript.msIO_getStdoutBufferBytes()))
		mapscript.msIO_resetHandlers()

		return result

	def render_vector_tile(self, node_id, zoom_level, min_x, min_y, max_x, max_y, layer_name):
		#we ASSume quite a bit here, postgis connection type and table structure

		#data = \
#"""wkb_geometry FROM (
#SELECT wkb_geometry, ogc_fid
#FROM %(table_name)s
#WHERE tile_x = %(x)d AND tile_y= %(y)d AND zoom_level = %(z)d
#) query using unique ogc_fid using srid=900915
#""" % {'table_name': table_name, 'z':z, 'x':x, 'y':y}
		#layer = self.mapfile.getLayerByName(layer_name)
		#layer.data = data
		layer = self.mapfile.getLayerByName(layer_name)
		layer.setFilter("([node_id] = %(node_id)d)" % {'node_id':node_id})

		return self.render_normal(None, None, None, None, min_x, min_y, max_x, max_y, zoom_level)

	def render(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		if(is_blank):
			return self.render_blank()
		elif(is_full):
			return self.render_full()
		return self.render_normal(geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level)

def render_vector_tiles(renderer, connect_str, table_name, layer_name):
	conn = connect(connect_str)
	curs = conn.cursor()

	curs.execute(\
"""
SELECT node_id, zoom_level,  min_x, min_y, max_x, max_y
FROM %(table_name)s
""" % {'table_name':table_name})

	start_time = time.time()
	processed_rows = 0

	for row in curs.fetchall():
		row = list(row) + [layer_name,]
		renderer.render_vector_tile(*row)

		processed_rows +=1
		if(processed_rows % 25 == 0):
			print processed_rows / (time.time() - start_time)

	print processed_rows / (time.time() - start_time)


