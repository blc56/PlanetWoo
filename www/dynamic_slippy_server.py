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
from planetwoo.www import load_config

class DynamicTileFetcher(tornado.web.RequestHandler):
	def initialize(self, storage_manager, layers, do_palette):
		self.storage_manager = storage_manager
		self.layers = layers
		self.do_palette = do_palette

	def get(self, zoom_level, x, y):
		zoom_level = int(zoom_level)
		x = int(x)
		y = int(y)

		img_file = self.storage_manager.dynamic_fetch(zoom_level, x, y, self.layers, self.do_palette)
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
	parser.add_argument('-C', '--config-file', dest='config_file', required=True)
	parser.add_argument('-R', '--force-create', action='store_true', dest='force_create', required=False,
			help='Drop/create all layers')
	parser.add_argument('-r', '--recreate_layers', nargs='+', dest='recreate_layers', required=False,
			help='List of layers to drop/create')
	parser.add_argument('-m', '--memcache', dest='memcache', required=False, nargs='+', help="List of memcached servers.")
	args = parser.parse_args()

	port = int(args.port)
	recreate_layers = []
	if(args.recreate_layers != None):
		recreate_layers = args.recreate_layers

	compositor, layer_groups = load_config(args.config_file, args.conn_str, args.force_create, recreate_layers, args.memcache)

	request_handlers = []
	for group_name in layer_groups:
		layers = layer_groups[group_name]['layer_order']
		do_palette = layer_groups[group_name].get('do_palette', True)

		url_prefix = args.url_prefix + group_name
		request_handlers .append(
			(r"%s([0-9]{1,2})/([0-9]{1,6})/([0-9]{1,6}).png" % url_prefix, DynamicTileFetcher,
				{'storage_manager':compositor, 'layers':layers, 'do_palette':do_palette}),
		)

	app = tornado.web.Application(request_handlers)

	app.listen(port, address=args.bind_address)
	tornado.ioloop.IOLoop.instance().start()

if(__name__ == '__main__'):
	main()

