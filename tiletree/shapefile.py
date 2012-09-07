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

##\file shapfile.py Shapefile classes for the tiletree module. 
import planetwoo.tiletree as tiletree
import shapely
import shapely.wkt
import shapely.geometry
import shapely.geometry.collection
import shapely.ops
try:
	import maptree
except:
	pass
from osgeo import ogr
from osgeo import osr
import copy

class ShapefileCutter:
	def __init__(self, shapefile_path, layer_name):
		self.shapefile_path = shapefile_path
		self.layer_name = layer_name

	def geom_generator(self):
		ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
		ogr_ds = ogr_driver.Open(self.shapefile_path)
		ogr_layer = ogr_ds.GetLayerByName(self.layer_name)

		f = ogr_layer.GetNextFeature()
		while(f):
			geom_ref = f.GetGeometryRef()
			if(geom_ref):
				yield shapely.wkt.loads(geom_ref.ExportToWkt())
			f = ogr_layer.GetNextFeature()

	def clone(self):
		return copy.deepcopy(self)

	def bbox(self):
		return self.geom.bounds

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):

		geom = parent_geom
		if(not parent_geom):
			geom = self.geom_generator()

		return tiletree.cut_helper(min_x, min_y, max_x, max_y, geom)

class ShapefileRAMCutter(ShapefileCutter):
	def __init__(self, shapefile_path, layer_name):
		ShapefileCutter.__init__(self, shapefile_path, layer_name)

	def load(self):
		ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
		ogr_ds = ogr_driver.Open(self.shapefile_path)
		ogr_layer = ogr_ds.GetLayerByName(self.layer_name)

		ret_geom = shapely.wkt.loads("POLYGON EMPTY")

		f = ogr_layer.GetNextFeature()
		while(f):
			geom_ref = f.GetGeometryRef()
			if(geom_ref):
				#yea, I should use cascaded union here, but it 
				#causes a segfault in my dev envrionment
				#TODO: fix that...
				ret_geom = ret_geom.union(shapely.wkt.loads(geom_ref.ExportToWkt()))
			f = ogr_layer.GetNextFeature()

		return ret_geom

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		geom = parent_geom
		if(parent_geom == None):
			geom = self.load()

		return tiletree.cut_helper(min_x, min_y, max_x, max_y, geom)


class MaptreeCutter:
	def __init__(self, shapefile_path, layer_name, qix_path):
		self.shp_tree = maptree.SHPTree(qix_path)
		self.ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
		self.ogr_ds = self.ogr_driver.Open(shapefile_path)
		self.layer = self.ogr_ds.GetLayerByName(layer_name)

	def clone(self):
		return copy.deepcopy(self)

	def bbox(self):
		raise Exception("Not Implemented")

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		fids = self.shp_tree.find_shapes(min_x, min_y, max_x, max_y)

		collection = ogr.CreateGeometryFromWkt("GEOMETRYCOLLECTION EMPTY")
		for fid in fids:
			f = self.layer.GetFeature(int(fid))
			geom_ref = f.GetGeometryRef()
			if(geom_ref):
				collection.AddGeometry(geom_ref)

		geom = shapely.wkt.loads(collection.ExportToWkt())

		#build a geometry from the bounds
		bbox = shapely.wkt.loads("POLYGON((%(min_x)s %(min_y)s, %(min_x)s %(max_y)s, %(max_x)s  %(max_y)s, %(max_x)s %(min_y)s, %(min_x)s %(min_y)s))" % 
			{'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y})
		#return geom
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

	def flush(self):
		pass
	
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

	def flush(self):
		pass
	
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


