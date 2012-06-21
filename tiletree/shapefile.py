##\file shapfile.py Shapefile classes for the tiletree module. 
import tiletree
import shapely
import shapely.wkt
import shapely.geometry
import shapely.geometry.collection
import shapely.ops
from osgeo import ogr
from osgeo import osr
import copy

class ShapefileCutter:
	def __init__(self, shapefile_path, layer_name, geom_type='polygon'):
		ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
		ogr_ds = ogr_driver.Open(shapefile_path)
		ogr_layer = ogr_ds.GetLayerByName(layer_name)

		collection = ogr.CreateGeometryFromWkt("GEOMETRYCOLLECTION EMPTY")
		f = ogr_layer.GetNextFeature()
		while(f):
			geom_ref = f.GetGeometryRef()
			if(geom_ref):
				collection.AddGeometry(geom_ref)
			f = ogr_layer.GetNextFeature()

		self.geom = shapely.wkt.loads(collection.ExportToWkt())

	def clone(self):
		return copy.deepcopy(self)

	def bbox(self):
		return self.geom.bounds

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		print "CUT"
		#build a geometry from the bounds
		bbox = shapely.wkt.loads("POLYGON((%(min_x)s %(min_y)s, %(min_x)s %(max_y)s, %(max_x)s  %(max_y)s, %(max_x)s %(min_y)s, %(min_x)s %(min_y)s))" % 
			{'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y})

		geom = parent_geom
		if(not parent_geom):
			geom = self.geom

		return bbox.intersection(geom)

class ShapefileStorageManager:
	def __init__(self, shapefile_path, layer_name, epsg_number=3395,
			fields=['node_id', 'zoom_level', 'tile_x', 'tile_y', 'is_leaf', 'is_blank', 'is_full',
				'min_x', 'min_y', 'max_x', 'max_y'],
			field_types={'min_x':'float', 'min_y':'float', 'max_x':'float', 'max_y':'float' },
			img_w=256, img_h=256):

		ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
		self.out_ds = ogr_driver.CreateDataSource(shapefile_path)
		srs = osr.SpatialReference()
		srs.ImportFromEPSG(epsg_number)
		self.out_layer = self.out_ds.CreateLayer(layer_name, srs, ogr.wkbUnknown)
		self.fields = fields
		self.img_w = img_w
		self.img_h = img_h

		ogr_field_types = {
			'int': ogr.OFTInteger,
			'float': ogr.OFTReal,
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
		#simplify the geometry appropriatley for this bounding box and
		#tile size before storing it
		simplify_factor = min(abs(node.max_x - node.min_x)/self.img_w,
				abs(node.max_y - node.min_y)/self.img_h)
		simplify_factor /= 2.0
		geom = node.geom.simplify(simplify_factor, preserve_topology=False)
		new_feature.SetGeometry(ogr.CreateGeometryFromWkt(shapely.wkt.dumps(geom)))
		self.out_layer.CreateFeature(new_feature)

	def lookup_tile(self, zoom_level, x, y):
		raise Exception("Not implemented")

	def close(self):
		self.out_ds.destroy()

class IndividualShapefileStorageManager:
	def __init__(self, layer_name, shapefile_prefix='shp_tiles/', epsg_number=3395,
			fields=['node_id', 'zoom_level', 'tile_x', 'tile_y', 'is_leaf', 'is_blank', 'is_full',
				'min_x', 'min_y', 'max_x', 'max_y'],
			field_types={'min_x':'float', 'min_y':'float', 'max_x':'float', 'max_y':'float' },
			img_w=256, img_h=256):

		self.shapefile_prefix = shapefile_prefix
		self.layer_name = layer_name
		self.ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
		self.srs = osr.SpatialReference()
		self.srs.ImportFromEPSG(epsg_number)
		self.fields = fields
		self.img_w = img_w
		self.img_h = img_h

		ogr_field_types = {
			'int': ogr.OFTInteger,
			'float': ogr.OFTReal,
		}

		self.field_dfns = []
		for f in self.fields:
			f_type = ogr_field_types.get(field_types.get(f, 'int'))
			field_dfn = ogr.FieldDefn(str(f), f_type)
			self.field_dfns.append(field_dfn)
	
	def store(self, node, img_bytes):
		if(node.is_blank or node.is_full):
			return

		shapefile_path = self.shapefile_prefix +\
			'_'.join([str(node.zoom_level),str(node.tile_x),str(node.tile_y)]) + '.shp'
		out_ds = self.ogr_driver.CreateDataSource(shapefile_path)
		out_layer = out_ds.CreateLayer(self.layer_name, self.srs, ogr.wkbUnknown)

		for dfn in self.field_dfns:
			out_layer.CreateField(dfn)

		new_feature = ogr.Feature(out_layer.GetLayerDefn())
		for f in self.fields:
			new_feature.SetField(str(f), getattr(node, f) )

		geom = node.geom
		#simplify the geometry appropriatley for this bounding box and
		#tile size before storing it
		#simplify_factor = min(abs(node.max_x - node.min_x)/self.img_w,
				#abs(node.max_y - node.min_y)/self.img_h)
		#simplify_factor /= 2.0
		#geom = node.geom.simplify(simplify_factor, preserve_topology=False)
		new_feature.SetGeometry(ogr.CreateGeometryFromWkt(shapely.wkt.dumps(geom)))
		out_layer.CreateFeature(new_feature)

	def lookup_tile(self, zoom_level, x, y):
		raise Exception("Not implemented")

	def close(self):
		pass


