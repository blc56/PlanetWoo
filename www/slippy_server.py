#!/usr/bin/env python
import sys
import tornado.ioloop
import tornado.web
import argparse

sys.path.append('../')
import tiletree
import tiletree.fsstorage
import tiletree.postgres

class TileFetcher(tornado.web.RequestHandler):
	def initialize(self, storage_manager):
		self.storage_manager = storage_manager

	def get(self, zoom_level, x, y):
		zoom_level = int(zoom_level)
		x = int(x)
		y = int(y)

		img_file = self.storage_manager.fetch(zoom_level, x, y)
		self.set_header('Content-Type', 'image/png')
		self.write(img_file.read())

def main():
	parser = argparse.ArgumentParser(description="planetwoo Slippy Map Server")
	parser.add_argument('-p', '--port', dest='port', required=True, action='store',)
	parser.add_argument('-t', '--tree-table', dest='tree_table', required=True, action='store',)
	parser.add_argument('-i', '--images-table', dest='images_table', required=True, action='store',)
	parser.add_argument('-u', '--url-prefix', dest='url_prefix', required=False, action='store',
		default='/slippy_map/')
	args = parser.parse_args()

	port = int(args.port)

	storage_manager =\
		tiletree.postgres.PostgresStorageManager(\
		'dbname=planetwoo user=guidek12',args.tree_table,args.images_table)

	app = tornado.web.Application([
		(r"%s([0-9]{1,2})/([0-9]{1,6})/([0-9]{1,6}).png" % args.url_prefix, TileFetcher,
			{'storage_manager':storage_manager}),
	])

	app.listen(port, address='127.0.0.1')
	tornado.ioloop.IOLoop.instance().start()

if(__name__ == '__main__'):
	main()

