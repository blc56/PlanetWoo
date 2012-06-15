##\file postgres.py storage classes for the tiletree module. 
import tiletree
from psycopg2 import *
import os.path
import math
import StringIO

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

	def copy(self, tree_file, image_file, with_header=True):
		curs = self.conn.cursor()	
		#read header lines
		tree_file.readline()
		image_file.readline()

		#print """COPY %s FROM '%s' WITH CSV HEADER"""% (self.node_table, tree_file_path)

		curs.copy_from(tree_file, self.node_table, ',', 'None')

		#use insert statements for now, because I'm too lazy to figure out how to 
		#copy from with bytea's
		#curs.copy_from(image_file, self.image_table, ',', 'None')
		values_generator = ( (l.split(',',1)[0], Binary(tiletree.decode_img_bytes(l.split(',',1)[1])) )
				for l in image_file )
		curs.executemany('INSERT INTO %s VALUES(%%s, %%s)' % self.image_table, values_generator)

		#curs.copy_from(\
#"""COPY %s FROM '%s' WITH CSV HEADER""" % (self.node_table, tree_file_path))
		#curs.copy_expert(\
#"""COPY %s FROM '%s' WITH CSV HEADER""" % (self.image_table, image_file_path))
		self.conn.commit()

	def fetch(self, zoom_level, x, y):
		#first, try to find the tile at this zoom level
		#if we don't then that means somewhere above us in the tree is a leaf node
		#find that leaf node and return its image
		curs = self.conn.cursor()

		print '===================='
		print zoom_level, x, y

		for z in range(zoom_level, -1, -1):
			print z, x, y
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
				if(z != zoom_level and result[1]):
					raise Exception("Tile not found")
				return StringIO.StringIO(result[0])

			x = int(math.floor(x/2.0))
			y = int(math.floor(y/2.0))

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

