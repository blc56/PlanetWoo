#!/usr/bin/env python
import sys
import tornado.ioloop
import tornado.web
import argparse

sys.path.append('../')
import tiletree
import tiletree.fsstorage
import tiletree.postgres
import tiletree.composite

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
	args = parser.parse_args()

	port = int(args.port)

	render_info_dict = {}
	render_layers = []
	for layer in args.layers:
		tree_table, image_table = layer.split(',')
		storage_manager = tiletree.postgres.PostgresStorageManager(args.conn_str, tree_table, image_table)
		render_info_dict[tree_table] = tiletree.composite.RenderInfo(layer, storage_manager, None, None, False)
		render_layers.append(tree_table)


	compositor = tiletree.composite.TileCompositor(render_info_dict, render_layers)

	app = tornado.web.Application([
		(r"%s([0-9]{1,2})/([0-9]{1,6})/([0-9]{1,6}).png" % args.url_prefix, TileFetcher,
			{'storage_manager':compositor, 'layers':render_layers}),
	])

	app.listen(port, address=args.bind_address)
	tornado.ioloop.IOLoop.instance().start()

if(__name__ == '__main__'):
	main()

