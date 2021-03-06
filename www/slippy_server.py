#!/usr/bin/env python
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

import sys
import tornado.ioloop
import tornado.web
import argparse

sys.path.append('../')
import tiletree
import tiletree.fsstorage
import tiletree.postgres
import tiletree.composite
import tiletree.memcached
import psycopg2

class TileFetcher(tornado.web.RequestHandler):
	def initialize(self, storage_manager, layers):
		self.storage_manager = storage_manager
		self.layers = layers

	def get(self, zoom_level, x, y):
		zoom_level = int(zoom_level)
		x = int(x)
		y = int(y)

		img_file = self.storage_manager.fetch(zoom_level, x, y, self.layers)
		self.set_header('Content-Type', 'image/png')
		self.write(img_file.read())

def main():
	parser = argparse.ArgumentParser(description="planetwoo Slippy Map Server")
	parser.add_argument('-p', '--port', dest='port', required=True, action='store',)
	parser.add_argument('-u', '--url-prefix', dest='url_prefix', required=False, action='store',
		default='/slippy_map/')
	parser.add_argument('-b', '--bind-address', dest='bind_address', required=False, action='store',
		default='127.0.0.1')
	parser.add_argument('-c', '--conn-str', dest='conn_str', required=False, action='store',
		default='dbname=planetwoo user=planetwoo')
	parser.add_argument('-l', '--layer', dest='layers', required=True, nargs='+', help="tree-table,image-table")
	parser.add_argument('-m', '--memcache', dest='memcache', required=False, nargs='+', help="List of memcached servers.")
	args = parser.parse_args()

	port = int(args.port)

	render_info_dict = {}
	render_layers = []
	print args.layers
	postgres_conn = psycopg2.connect(args.conn_str)
	for layer in args.layers:
		tree_table, image_table = layer.split(',')
		storage_manager = tiletree.postgres.PostgresStorageManager(None, tree_table, image_table, postgres_conn)
		render_info_dict[tree_table] = tiletree.composite.RenderInfo(layer, storage_manager, None, None, False)
		render_layers.append(tree_table)


	compositor = tiletree.composite.TileCompositor(render_info_dict, render_layers)
	if(args.memcache != None):
		compositor = tiletree.memcached.MCDStorageManager(compositor, args.memcache, render_layers)

	app = tornado.web.Application([
		(r"%s([0-9]{1,2})/([0-9]{1,6})/([0-9]{1,6}).png" % args.url_prefix, TileFetcher,
			{'storage_manager':compositor, 'layers':render_layers}),
	])

	app.listen(port, address=args.bind_address)
	tornado.ioloop.IOLoop.instance().start()

if(__name__ == '__main__'):
	main()

