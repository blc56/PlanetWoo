##\file shapfile.py Shapefile classes for the tiletree module. 
import tiletree
import shapely
import shapely.wkt
import shapely.geometry
import shapely.geometry.collection
import shapely.ops
from osgeo import ogr

class ShapefileCutter:
	def __init__(self, shapefile_path, layer_name):
		ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
		ogr_ds = ogr_driver.Open(shapefile_path)
		ogr_layer = ogr_ds.GetLayerByName(layer_name)

		shapes = []
		f = ogr_layer.GetNextFeature()
		while(f):
			this_wkt = f.GetGeometryRef().ExportToWkt()
			shapes.append(shapely.wkt.loads(this_wkt))
			f = ogr_layer.GetNextFeature()

		self.geom = shapely.ops.cascaded_union(shapes)

	def bbox(self):
		return self.geom.bounds

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		#build a geometry from the bounds
		bbox = shapely.wkt.loads("POLYGON((%(min_x)s %(min_y)s, %(min_x)s %(max_y)s, %(max_x)s  %(max_y)s, %(max_x)s %(min_y)s, %(min_x)s %(min_y)s))" % 
			{'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y})

		geom = parent_geom
		if(not parent_geom):
			geom = self.geom

		return bbox.intersection(geom)

