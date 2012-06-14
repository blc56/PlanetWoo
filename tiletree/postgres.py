##\file postgres.py storage classes for the tiletree module. 
import tiletree
from psycopg2 import *
import os.path
import math

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
is_full BOOLEAN
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

	def fetch(self, zoom_level, x, y):
		#first, try to find the tile at this zoom level
		#if we don't then that means somewhere above us in the tree is a leaf node
		#find that leaf node and return its image
		curs = self.conn.cursor()

		print '===================='
		print zoom_level, x, y

		for z in range(zoom_level, -1, -1):
		#for z in [zoom_level]:

			print z, x, y

			#curs.execute("SELECT * from %(table)s WHERE zoom_level = %%(z)s and tile_x = %%(x)s and tile_y = %%(y)s" % {'table': self.node_table}, {'z': z, 'x': x, 'y': y})
			#node = curs.fetchone()
			#if(node):
				#print node[4]
				#return open(self.get_image_path(node[4]), 'r')

			x = math.floor(x/2.0)
			y = math.floor(y/2.0)

		raise Exception("Tile not found")

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

		#if we are using a SplitStorageManager
		#then we can find out a node is blank or full
		#after we already stored id
		if(node.is_blank or node.is_full):
			curs.execute("DELETE FROM %s WHERE node_id = %%s"\
					% (self.node_table,), (node.node_id,))
			curs.execute("DELETE FROM %s WHERE image_id = %%s"\
					% (self.image_table,), (node.node_id,))

		curs.execute(\
"""
INSERT INTO %s VALUES(%%(node_id)s, %%(zoom_level)s, %%(tile_x)s,
%%(tile_y)s, %%(image_id)s, %%(is_leaf)s, %%(is_blank)s, %%(is_full)s)
""" % (self.node_table,), {
		'node_id':node.node_id, 'zoom_level':node.zoom_level, 'tile_x':node.tile_x,
		'tile_y':node.tile_y, 'image_id':node.image_id, 'is_leaf':node.is_leaf, 'is_blank':node.is_blank, 'is_full':node.is_full})


	def store(self, node, img_bytes):
		self.store_node(node)
		self.store_image(node, img_bytes)
		self.conn.commit()

	def close(self):
		#self.conn.commit()
		pass

