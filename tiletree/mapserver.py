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

		#creating a mapfile leaks memory, so only create it once
		template_args = {
			#'wkt': shapely.wkt.dumps(geometry),
			#'shapefile_path' : shapefile_path
		}
		self.mapfile = mapscript.fromstring(self.mapfile_template % template_args)

	def render_normal(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		mapscript.msIO_installStdoutToBuffer()
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

		self.mapfile.OWSDispatch(wms_req)

		mapscript.msIO_stripStdoutBufferContentType()

		img_id = self.next_img_id
		self.next_img_id += 1

		result =  (img_id,
				StringIO.StringIO(mapscript.msIO_getStdoutBufferBytes()))
		mapscript.msIO_resetHandlers()

		return result

	def render(self, geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level):
		if(is_blank):
			return self.render_blank()
		elif(is_full):
			return self.render_full()
		return self.render_normal(geometry, is_blank, is_full, is_leaf, min_x, min_y, max_x, max_y, zoom_level)

