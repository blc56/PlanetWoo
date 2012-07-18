#!/usr/bin/env python
import sys
import tornado.ioloop
import tornado.web
import argparse
import json

sys.path.append('../')
import tiletree
import tiletree.mapserver
import tiletree.postgres
import tiletree.composite

class DynamicTileFetcher(tornado.web.RequestHandler):
	def initialize(self, storage_manager):
		self.storage_manager = storage_manager

	def get(self, zoom_level, x, y):
		zoom_level = int(zoom_level)
		x = int(x)
		y = int(y)

		img_file = self.storage_manager.dynamic_fetch(zoom_level, x, y)
		self.set_header('Content-Type', 'image/png')
		self.write(img_file.read())

def load_config(config_path, conn_str):
	config = json.loads(open(config_path, 'r').read())
	cutters = []
	renderers = []
	storage_managers = []
	for layer in config['layer_order']:
		layer = config[layer]
		cutters.append(tiletree.NullGeomCutter())
		renderers.append(tiletree.mapserver.MapServerRenderer(open(layer['mapfile'],'r').read(), layer['layers']))
		storage_managers.append(tiletree.postgres.PostgresStorageManager(conn_str, layer['tree_table'],
			layer['image_table']))

	return tiletree.composite.TileCompositor(storage_managers, renderers, cutters, config['extent'])

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
	args = parser.parse_args()

	port = int(args.port)

	compositor = load_config(args.config_file, args.conn_str)

	app = tornado.web.Application([
		(r"%s([0-9]{1,2})/([0-9]{1,6})/([0-9]{1,6}).png" % args.url_prefix, DynamicTileFetcher,
			{'storage_manager':compositor}),
	])

	app.listen(port, address=args.bind_address)
	tornado.ioloop.IOLoop.instance().start()

if(__name__ == '__main__'):
	main()

