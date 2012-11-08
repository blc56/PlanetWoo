#!/usr/bin/env python
import multiprocessing
import multiprocessing.pool
import time
import argparse
import urllib2
import random
import copy
import sys
import math
import json

TILE_WIDTH = 8
TILE_HEIGHT = 4
TILE_FACTOR = 12 
MAX_DEPTH = 16
MAP_EXTENT = [-7081604, -5235222, 4868396, 6714778]

#http://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic
class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False
    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)

# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess

def generate_test_coordinates(tile_width=TILE_WIDTH, tile_height=TILE_HEIGHT, max_depth=MAX_DEPTH, ):
	z = random.randint(4, max_depth)
	x = random.randint(tile_width, 2**z - tile_width)
	y = random.randint(tile_height, 2**z - tile_height)
	return (z, x, y)

def read_test_coordinates(in_file, num_flogs, max_depth=MAX_DEPTH, tile_width=TILE_WIDTH, tile_height=TILE_HEIGHT, map_extent=MAP_EXTENT):
	test_coords = []
	for x in range(0,num_flogs):
		extent_line = in_file.readline()
		extent = json.loads(extent_line)
		#find the smallest zoom level that will contain this extent
		target_tile_size = min((extent[2] - extent[0])/float(tile_width), (extent[3] - extent[1]) / float(tile_height))
		if(target_tile_size == 0):
			continue
		zoom = math.ceil( math.log((map_extent[2]-map_extent[0])/target_tile_size, 2) ) 
		zoom = min(zoom, max_depth)
		tile_size = (map_extent[3] - map_extent[0]) / float(2**zoom)
		x = int(round( ((extent[2] + extent[0])/2.0) - map_extent[0] ) / tile_size)
		y = int(round( (map_extent[3] - (extent[3] + extent[1])/2.0)) / tile_size)
		test_coords.append((zoom, x, y))

	return test_coords
	

def slippy_test_helper(url):
	try:
		#print url_prefix + '%d/%d/%d.png' % (z, x_pos, y_pos)
		request = urllib2.urlopen(url)
		return True
	except:
		return False

def slippy_test(test_options, width=TILE_WIDTH, height=TILE_HEIGHT, tile_factor=TILE_FACTOR):
	#assume each screen is a 10x5 grid of tiles
	#this approximately the OTM map size at full screen
	#at my desk
	z = test_options['z']
	x = test_options['x']
	y = test_options['y']
	url_prefix = test_options['url_prefix']


	tiles_to_request = []
	for x_iter in range(x - width/2, x + width/2 - 1):
		for y_iter in range(y - height/2, y + height/2 - 1):
			tiles_to_request.append(url_prefix + '%d/%d/%d.png' % (z, x_iter, y_iter))

	pool = multiprocessing.Pool(processes=tile_factor)
	start_time = time.time()
	results = pool.map(slippy_test_helper, tiles_to_request)
	end_time = time.time()
	pool.close()
	pool.join()
	sys.stderr.write('.')

	if(False in results):
		return '%d,ERROR,%d' % (float('nan'), float('nan'))
	return '%d,OK,' % z + str(end_time - start_time)


def get_test_func(test_type):
	if(test_type == 'slippy'):
		return slippy_test
	
	raise Exception('Invalid test type')

def get_test_func_args(test_type, z, x, y, url_prefix):
	if(test_type == 'slippy'):
		return {
			'url_prefix': url_prefix,
			'x':x,
			'y':y,
			'z':z,
		}

	raise Exception('Invalid test type')

def main():
	parser = argparse.ArgumentParser(description="""Flogger de maps!""")
	parser.add_argument('-n', '--num_flogs', dest='num_flogs', required=True, help='How many tests?', type=int)
	parser.add_argument('-t', '--num_threads', dest='num_threads', required=True, help='How many thread?', type=int)
	parser.add_argument('-i', '--num_iterations', dest='num_iterations', required=True, help='Repeat flogs how many times?', type=int)
	parser.add_argument('-f', '--input_file', dest='input_file', default=None, required=False)
	parser.add_argument('-u', '--url_prefix', dest='url_prefix', default=None, required=True,
			help='URL prefix', type=unicode)
	parser.add_argument('-e', '--map_extent', dest='map_extent', default=json.dumps(MAP_EXTENT), required=False,
			help='Map extent (in json)', type=unicode)
	parser.add_argument('-m', '--max_depth', dest='max_depth', default=19, type=int, required=False,
			help='Maximum zoom level')
	args = parser.parse_args()

	map_extent = json.loads(args.map_extent)

	#calculate a  list of test coordinates
	test_coords = []
	if(args.input_file == None):
		test_coords = [generate_test_coordinates(max_depth=args.max_depth) for x in range(args.num_flogs)]
	else:
		test_coords = read_test_coordinates(open(args.input_file,'r'), args.num_flogs, max_depth=args.max_depth, map_extent=map_extent)

	test_func_slippy = get_test_func('slippy')
	test_args_slippy = [get_test_func_args('slippy', *c, url_prefix=args.url_prefix) for c in test_coords] * args.num_iterations

	pool = MyPool(processes=args.num_threads)
	begin = time.time()
	slippy_results = pool.map(test_func_slippy, test_args_slippy)
	end = time.time()
	pool.close()
	pool.join()
	sys.stderr.write('SLIPPY MAP!!!! ')
	sys.stderr.write(str(end - begin))
	sys.stderr.write('\n')
	sys.stderr.write('===================================\n')
	sys.stderr.write('\n')

	print '\n'.join(slippy_results)

if( __name__ == '__main__'):

	main()

