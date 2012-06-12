##\file postgres.py storage classes for the tiletree module. 
import tiletree
from psycopg2 import *
import os.path
import math

class PostgresStorageManager:
	def __init__(self, connect_str, table, image_dir='images', image_suffix='.png'):
		self.conn = connect(connect_str)
		self.table = table
		self.image_dir = image_dir
		self.image_suffix = image_suffix

	def get_image_path(self, image_id):
		return os.path.join(self.image_dir, str(image_id)) + self.image_suffix

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

			curs.execute("SELECT * from %(table)s WHERE zoom_level = %%(z)s and tile_x = %%(x)s and tile_y = %%(y)s" % {'table': self.table}, {'z': z, 'x': x, 'y': y})
			node = curs.fetchone()
			if(node):
				print node[4]
				return open(self.get_image_path(node[4]), 'r')

			x = math.floor(x/2.0)
			y = math.floor(y/2.0)

		raise Exception("Tile not found")


	def store(self, node, img_bytes):
		pass

	def close(self):
		pass

