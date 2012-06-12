##\file shapfile.py Shapefile classes for the tiletree module. 
import tiletree
import shapely
import shapely.wkt
import shapely.geometry
import shapely.geometry.collection
import shapely.ops
from osgeo import ogr
from osgeo import osr

class ShapefileCutter:
	def __init__(self, shapefile_path, layer_name):
		ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
		ogr_ds = ogr_driver.Open(shapefile_path)
		ogr_layer = ogr_ds.GetLayerByName(layer_name)

		shapes = []
		f = ogr_layer.GetNextFeature()
		while(f):
			geom_ref = f.GetGeometryRef()
			if(geom_ref):
				this_wkt = geom_ref.ExportToWkt()
			else:
				this_wkt = "GEOMETRYCOLLECTION EMPTY"
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

class ShapefileStorageManager:
	def __init__(self, shapefile_path, layer_name, epsg_number=3395,
			fields=['node_id', 'zoom_level', 'tile_x', 'tile_y', 'is_leaf', 'is_blank', 'is_full'],
			field_types={}):

		ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
		self.out_ds = ogr_driver.CreateDataSource(shapefile_path)
		srs = osr.SpatialReference()
		srs.ImportFromEPSG(epsg_number)
		self.out_layer = self.out_ds.CreateLayer(layer_name, srs, ogr.wkbUnknown)
		self.fields = fields

		ogr_field_types = {
			'int': ogr.OFTInteger,
		}

		for f in self.fields:
			f_type = ogr_field_types.get(field_types.get(f, 'int'))
			field_dfn = ogr.FieldDefn(str(f), f_type)
			self.out_layer.CreateField(field_dfn)
	
	def store(self, node, img_bytes):
		new_feature = ogr.Feature(self.out_layer.GetLayerDefn())
		for f in self.fields:
			new_feature.SetField(str(f), getattr(node, f) )

		geom = node.geom
		new_feature.SetGeometry(ogr.CreateGeometryFromWkt(shapely.wkt.dumps(geom)))
		self.out_layer.CreateFeature(new_feature)

	def lookup_tile(self, zoom_level, x, y):
		raise Exception("Not implemented")

	def close(self):
		self.out_ds.destroy()


