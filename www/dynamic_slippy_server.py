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
import tiletree.label
from scripts.render_to_csv import load_cutter

class DynamicTileFetcher(tornado.web.RequestHandler):
	def initialize(self, storage_manager, layers):
		self.storage_manager = storage_manager
		self.layers = layers

	def get(self, zoom_level, x, y):
		zoom_level = int(zoom_level)
		x = int(x)
		y = int(y)

		img_file = self.storage_manager.dynamic_fetch(zoom_level, x, y, self.layers)
		self.set_header('Content-Type', 'image/png')
		self.write(img_file.read())

def load_config(config_path, conn_str):
	config = json.loads(open(config_path, 'r').read())
	render_infos = {}

	for layer_name in config['layer_order']:
		layer = config[layer_name]
		cutter = load_cutter(layer)
		renderer = tiletree.mapserver.MapServerRenderer(open(layer['mapfile'],'r').read(), layer['layers'])
		storage_manager = tiletree.postgres.PostgresStorageManager(conn_str, layer['tree_table'],
			layer['image_table'])
		render_infos[layer_name] = tiletree.composite.RenderInfo(storage_manager, renderer, cutter,
			layer.get('check_full', True), layer.get('start_zoom', None), layer.get('stop_zoom', None))

	for layer_name in config['label_order']:
		layer = config[layer_name]
		cutter = load_cutter(layer)
		feature_storage_manager = tiletree.postgres.PostgresStorageManager(conn_str, layer['tree_table'],
			layer['image_table'])
		renderer = tiletree.label.LabelRenderer(open(layer['mapfile'],'r').read(), feature_storage_manager)

		render_infos['label_' + layer_name] = tiletree.composite.RenderInfo(None, renderer, cutter,
			layer.get('check_full', True), layer.get('start_zoom', None), layer.get('stop_zoom', None))

	layer_list = config['layer_order'] + ['label_' + x for x in config['label_order']]

	return (tiletree.composite.TileCompositor(render_infos, config['extent']), layer_list)

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

	compositor, layers = load_config(args.config_file, args.conn_str)

	app = tornado.web.Application([
		(r"%s([0-9]{1,2})/([0-9]{1,6})/([0-9]{1,6}).png" % args.url_prefix, DynamicTileFetcher,
			{'storage_manager':compositor, 'layers':layers}),
	])

	app.listen(port, address=args.bind_address)
	tornado.ioloop.IOLoop.instance().start()

if(__name__ == '__main__'):
	main()

