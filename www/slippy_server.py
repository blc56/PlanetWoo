#!/usr/bin/env python
import sys
import tornado.ioloop
import tornado.web

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
	port = 8080
	storage_manager =\
		tiletree.postgres.PostgresStorageManager(\
		'dbname=planetwoo user=guidek12','north_america_tree',
		image_dir='/srv/excensus/planetwoo/planetwoo/tests/unit/images/')
		#tiletree.fsstorage.FSStorageManager(image_prefix='/srv/excensus/planetwoo/planetwoo/tests/unit/images/')

	app = tornado.web.Application([
		(r"/slippy_map/([0-9]{1,2})/([0-9]{1,6})/([0-9]{1,6}).png", TileFetcher,
			{'storage_manager':storage_manager}),
	])

	app.listen(port, address='127.0.0.1')
	tornado.ioloop.IOLoop.instance().start()

if(__name__ == '__main__'):
	main()

