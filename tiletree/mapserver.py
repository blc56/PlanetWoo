##\file mapserver.py render classes for the tiletree module. 
from tiletree import *
import shapely
import shapely.wkt
import shapely.geometry

class MapServerRenderer(NullRenderer):
	def __init__(self, mapfile_template, layers, img_w=256, img_h=256, img_prefix='images/'):
		NullRenderer.__init__(self, img_w, img_h, img_prefix)
		self.mapfile_template=mapfile_template
		self.layers=layers

	def tile_info(self, geometry, min_x, min_y, max_x, max_y, zoom_level):
		is_blank = False
		is_full = False
		is_leaf = False
		if(geometry == None or geometry.is_empty):
			is_blank = True
			#is_leaf = True

		bbox = shapely.wkt.loads("POLYGON((%(min_x)s %(min_y)s, %(min_x)s %(max_y)s, %(max_x)s  %(max_y)s, %(max_x)s %(min_y)s, %(min_x)s %(min_y)s))" % 
			{'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y})

		if(geometry.contains(bbox)):
			is_full = True
			#is_leaf = True

		return (is_blank, is_full, is_leaf)

	def render_normal(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		wms_req = mapscript.OWSRequest()

		template_args = {
			'wkt': shapely.wkt.dumps(geometry),
		}
		mapfile = mapscript.fromstring(self.mapfile_template % template_args)

		wms_req.setParameter('MODE', 'WMS')
		wms_req.setParameter('VERSION', '1.1.1')
		wms_req.setParameter('FORMAT', 'image/png')
		wms_req.setParameter('TRANSPARENT', 'TRUE')
		wms_req.setParameter('WIDTH', str(self.img_w))
		wms_req.setParameter('HEIGHT', str(self.img_h))
		wms_req.setParameter('SRS', 'EPSG:3857')
		wms_req.setParameter('REQUEST', 'GetMap')
		wms_req.setParameter('BBOX', ','.join(str(x) for x in [min_x, min_y, max_x, max_y]))
		wms_req.setParameter('LAYERS', self.layers)

		mapscript.msIO_installStdoutToBuffer()
		mapfile.OWSDispatch(wms_req)
		mapscript.msIO_stripStdoutBufferContentType()

		img_id = self.next_img_id
		self.next_img_id += 1

		return (img_id, StringIO.StringIO(mapscript.msIO_getStdoutBufferBytes()))

