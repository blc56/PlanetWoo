##\file postgres.py storage classes for the tiletree module. 
import tiletree
from psycopg2 import *
import os.path
import math
import StringIO
import shapely.wkb

class PostgresStorageManager:
	def __init__(self, connect_str, node_table, image_table):
		self.conn = connect(connect_str)
		self.node_table = node_table
		self.image_table = image_table

	def recreate_tables(self):
		curs = self.conn.cursor()	
		curs.execute(\
"""
DROP TABLE IF EXISTS %s
""" % (self.node_table,))
		curs.execute(\
"""
DROP TABLE IF EXISTS %s
""" % (self.image_table,))

		curs.execute(\
"""
CREATE TABLE %s 
(
node_id BIGINT PRIMARY KEY,
zoom_level INTEGER,
tile_x INTEGER,
tile_y INTEGER,
image_id BIGINT,
is_leaf BOOLEAN,
is_blank BOOLEAN,
is_full BOOLEAN,
metadata VARCHAR(512)
);
""" % (self.node_table,))

		curs.execute(\
"""
CREATE TABLE %s 
(
image_id BIGINT PRIMARY KEY,
img_bytes BYTEA
);
""" % (self.image_table,))
		self.conn.commit()

	def copy(self, tree_file, image_file, with_header=True):
		curs = self.conn.cursor()	
		#read header lines
		tree_file.readline()
		image_file.readline()

		curs.copy_from(tree_file, self.node_table, ',', 'None')

		#have we inserted a blank image yet?
		curs.execute('SELECT count(*) from %s where image_id = -1' % self.image_table)
		have_blank = bool(curs.fetchone()[0])

		#have we inserted a full image yet?
		curs.execute('SELECT count(*) from %s where image_id = -2' % self.image_table)
		have_full = bool(curs.fetchone()[0])

		for line in image_file:
			image_id, image_bytes = line.split(',',1)
			image_id = int(image_id)

			if(image_id == -1):
				if(have_blank):
					continue
				have_blank=True

			elif(image_id == -2):
				if(have_full):
					continue
				have_full=True

			image_bytes = tiletree.decode_img_bytes(image_bytes)
			curs.execute('INSERT INTO %s VALUES(%%s, %%s)' % (self.image_table,),
				(image_id, Binary(image_bytes)) )

		self.conn.commit()

	def fetch_info(self, zoom_level, x, y):
		#first, try to find the tile at this zoom level
		#if we don't then that means somewhere above us in the tree is a leaf node
		curs = self.conn.cursor()

		for z in range(zoom_level, -1, -1):
			node_id = tiletree.build_node_id(z, x, y)
			curs.execute(\
	"""
	SELECT nodes.is_blank, nodes.is_full, nodes.is_leaf, nodes.metadata
	FROM %s nodes
	WHERE nodes.node_id = %%s
	""" % (self.node_table,), (node_id,) )
			result = curs.fetchone()
			if(result):
				return result

			x = int(math.floor(x/2.0))
			y = int(math.floor(y/2.0))

		raise tiletree.TileNotFoundException()

	def fetch(self, zoom_level, x, y):
		#first, try to find the tile at this zoom level
		#if we don't then that means somewhere above us in the tree is a leaf node
		#find that leaf node and return its image
		curs = self.conn.cursor()

		#print '===================='
		#print zoom_level, x, y

		for z in range(zoom_level, -1, -1):
			#print z, x, y
			node_id = tiletree.build_node_id(z, x, y)

			curs.execute(\
"""
SELECT images.img_bytes, (nodes.is_leaf and (nodes.is_full or nodes.is_blank))
FROM %s nodes, %s images
WHERE nodes.node_id = %%s AND images.image_id = nodes.image_id
""" % (self.node_table, self.image_table,), (node_id,) )
			result = curs.fetchone()
			if(result):
				#if we end up pulling an image from a node at a higher
				#zoom level, it should be a leaf node
				if(z != zoom_level and not result[1]):
					raise tiletree.TileNotFoundException()
				return StringIO.StringIO(result[0])

			x = int(math.floor(x/2.0))
			y = int(math.floor(y/2.0))

		raise tiletree.TileNotFoundException()

	def store_image(self, node, img_bytes):
		curs = self.conn.cursor()
		if(node.image_id == -1 or node.image_id == -2):
			return 

		curs.execute(\
"""
INSERT INTO %s VALUES(%%s, %%s)
""" % (self.image_table,), (node.image_id, Binary(img_bytes.getvalue()) ) )

	def store_node(self, node):
		curs = self.conn.cursor()

		curs.execute(\
"""
INSERT INTO %s VALUES(%%(node_id)s, %%(zoom_level)s, %%(tile_x)s,
%%(tile_y)s, %%(image_id)s, %%(is_leaf)s, %%(is_blank)s, %%(is_full)s, %%(metadata)s)
""" % (self.node_table,), node.to_dict())


	def store(self, node, img_bytes):
		self.store_node(node)
		self.store_image(node, img_bytes)
		self.conn.commit()

	def flush(self):
		self.conn.commit()

	def close(self):
		#self.conn.commit()
		pass

class PostgresCutter:
	def __init__(self, conn_str, table_name, geo_col="wkb_geometry", input_srid='-1'):
		self.conn_str = conn_str
		self.conn = connect(self.conn_str)
		self.curs = self.conn.cursor()
		self.table_name = table_name
		self.geo_col = geo_col
		self.input_srid = input_srid

	def bbox(self):
		raise Exception("Not implemented")

	def clone(self):
		return PostgresCutter(self.conn_str, self.table_name, self.geo_col, self.input_srid)

	def cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		geom = parent_geom
		if(geom == None):
			geom = self.db_cut(min_x, min_y, max_x, max_y)

		return tiletree.cut_helper(min_x, min_y, max_x, max_y, geom)

	def db_cut(self, min_x, min_y, max_x, max_y, parent_geom=None):
		self.curs.execute(\
"""
SELECT ST_AsBinary(%(geo_col)s)
FROM "%(table)s" WHERE ST_Intersects( %(geo_col)s, ST_GeomFromText(
'POLYGON( ( %%(min_x)s %%(min_y)s, %%(max_x)s %%(min_y)s, %%(max_x)s %%(max_y)s,
%%(min_x)s %%(max_y)s, %%(min_x)s %%(min_y)s ) )',
%%(srid)s) ) """ % {'table': self.table_name, 'geo_col':self.geo_col}, {'min_x':min_x, 'min_y':min_y,
	'max_x':max_y, 'max_y':max_y, 'srid':self.input_srid})

		result = (shapely.wkb.loads(str(x[0])) for x in self.curs.fetchall())

		return result

