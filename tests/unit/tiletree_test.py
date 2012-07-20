#!/usr/bin/env python
import sys
sys.path.append('../../')
import tiletree
import tiletree.fsstorage
import tiletree.csvstorage
import tiletree.mapserver
import tiletree.shapefile
import tiletree.postgres
import tiletree.splitstorage
import tiletree.label
import StringIO
import os.path

def null_test():
	print "Null test"
	storage_manager = tiletree.NullStorageManager()
	renderer = tiletree.NullRenderer()
	cutter = tiletree.NullGeomCutter()
	min_x = 0
	min_y = 0
	max_x = 10
	max_y = 10
	tiletree.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, stop_level=5)

def null_fs_tree_test():
	print "Null fs tree test"
	storage_manager = tiletree.fsstorage.FSStorageManager(image_prefix='test_images/')

	if(os.path.exists('test_images')):
		raise Exception("Directory already exists!")
	os.makedirs('test_images')

	renderer = tiletree.NullRenderer()
	cutter = tiletree.NullGeomCutter()
	tiletree.generate(0, 0, 10, 10, storage_manager, renderer, cutter, stop_level=2)

def null_csv_tree_test():
	print "Null csv tree test"
	storage_manager = tiletree.csvstorage.CSVStorageManager(open('null_csv_tree.csv','w'), open('null_csv_images.csv', 'w'))
	renderer = tiletree.NullRenderer()
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	min_x, min_y, max_x, max_y = (-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	tiletree.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, stop_level=2)

def shapefile_cutter_test():
	print "Shapefile cutter test"
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	#print cutter.geom.area, cutter.geom.bounds
	geom = cutter.cut(-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	#print geom.area, geom.bounds

#def maptree_cutter_test():
	#print "Maptree cutter test"
	#cutter = tiletree.shapefile.MaptreeCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america', 'test_geo/webmerc_northamerica/north_america.qix')
	#geom = cutter.cut(-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	#print geom.area, geom.bounds

def mapserver_render_test():
	print "Mapserver render test"
	storage_manager = tiletree.csvstorage.CSVStorageManager(open('mapserver_tree.csv','w'), open('mapserver_images.csv', 'w'))
	#storage_manager = tiletree.fsstorage.FSStorageManager(image_prefix='test_images/')
	renderer = tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),['poly_fill'], img_w=256, img_h=256)
	min_x, min_y, max_x, max_y = (-19338083.638408754, 804303.8439259261, -2215605.96243665, 17926781.51989803)
	tiletree.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, tiletree.NullGeomCutter(), stop_level=3)

def postgres_test():
	print "Postgres test"
	storage_manager = tiletree.postgres.PostgresStorageManager('dbname=planetwoo user=planetwoo', 'tile_nodes', 'tile_images')
	storage_manager.recreate_tables()
	storage_manager.store(tiletree.QuadTreeGenNode(), StringIO.StringIO(''))
	storage_manager.close()

#def geom_builder_csv_test():
	#print "Geom builder csv test"
	#storage_manager = tiletree.csvstorage.CSVStorageManager(open('geom_tree.csv','w'), None,
			#fields=['node_id', 'zoom_level', 'tile_x', 'tile_y',
				#'min_x', 'min_y', 'max_x', 'max_y', 'is_leaf', 'is_blank', 'is_full', 'geom'])
	#renderer = tiletree.NullRenderer()
	#cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	#min_x, min_y, max_x, max_y = (-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	#tiletree.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, stop_level=3)

#def geom_builder_shapefile_test():
	#print "Geom builder shapefile test"
	#storage_manager = tiletree.shapefile.ShapefileStorageManager('tile_geom.shp', 'tile_geom')
	#renderer = tiletree.NullRenderer()
	#cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	#min_x, min_y, max_x, max_y = (-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	#tiletree.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, stop_level=3)

#def individual_geom_builder_shapefile_test():
	#print "Individual geom builder shapefile test"
	#storage_manager = tiletree.shapefile.IndividualShapefileStorageManager('tile_geom', 'shp_tiles/')

	#if(os.path.exists('shp_tiles')):
		#raise Exception("Directory already exists!")
	#os.makedirs('shp_tiles')

	#renderer = tiletree.NullRenderer()
	#cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	#min_x, min_y, max_x, max_y = (-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	#tiletree.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, stop_level=3)

def meta_tile_mapserver_test():
	print "Meta tile mapserver test"
	backend_storage_manager = tiletree.csvstorage.CSVStorageManager(open('meta_tile_mapserver_tree.csv','w'), open('meta_tile_mapserver_images.csv', 'w'))
	storage_manager = tiletree.splitstorage.SplitStorageManager(backend_storage_manager, 3)
	cutter = tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america')
	renderer = tiletree.mapserver.MapServerRenderer(open('split_default.map','r').read(),['poly_fill'], img_w=256, img_h=256)
	min_x, min_y, max_x, max_y = (-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	tiletree.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, cutter, stop_level=4)
	backend_storage_manager.close()

def mapserver_mt_test():
	print "Mapserver multithreaded test"
	#use a node the calculate the parameters for each job
	total_bbox = (-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	root_node = tiletree.QuadTreeGenNode(min_x=total_bbox[0], min_y=total_bbox[1], max_x=total_bbox[2], max_y=total_bbox[3])
	job_nodes = root_node.split()
	stop_level = 2

	storage_manager0 = tiletree.csvstorage.CSVStorageManager(open('mt_mapserver_tree_0.csv','w'), open('mt_mapserver_images_0.csv', 'w'))
	storage_manager1 = tiletree.csvstorage.CSVStorageManager(open('mt_mapserver_tree_1.csv','w'), open('mt_mapserver_images_1.csv', 'w'))
	storage_manager2 = tiletree.csvstorage.CSVStorageManager(open('mt_mapserver_tree_2.csv','w'), open('mt_mapserver_images_2.csv', 'w'))
	storage_manager3 = tiletree.csvstorage.CSVStorageManager(open('mt_mapserver_tree_3.csv','w'), open('mt_mapserver_images_3.csv', 'w'))

	jobs = []
	jobs.append( job_nodes[0].to_generator_job(storage_manager0,
			tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),['poly_fill'], img_w=256, img_h=256),
			tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america'),
			stop_level) )
	jobs.append( job_nodes[1].to_generator_job(storage_manager1,
			tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),['poly_fill'], img_w=256, img_h=256),
			tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america'),
			stop_level) )
	jobs.append( job_nodes[2].to_generator_job(storage_manager2,
			tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),['poly_fill'], img_w=256, img_h=256),
			tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america'),
			stop_level) )
	jobs.append( job_nodes[3].to_generator_job(storage_manager3,
			tiletree.mapserver.MapServerRenderer(open('default.map','r').read(),['poly_fill'], img_w=256, img_h=256),
			tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america'),
			stop_level) )

	tiletree.generate_mt(jobs, num_threads=4)

def meta_mapserver_mt_test():
	print "Mapserver multithreaded test"
	#use a node the calculate the parameters for each job
	total_bbox = (-15696351.547463987, 804303.8439259261, -5857338.053381417, 17926781.51989803)
	root_node = tiletree.QuadTreeGenNode(min_x=total_bbox[0], min_y=total_bbox[1], max_x=total_bbox[2], max_y=total_bbox[3])
	job_nodes = root_node.split()
	stop_level = 4

	backend_storage_manager0 = tiletree.csvstorage.CSVStorageManager(open('meta_mt_mapserver_tree_0.csv','w'), open('mt_mapserver_images_0.csv', 'w'))
	storage_manager0 = tiletree.splitstorage.SplitStorageManager(backend_storage_manager0, 3)

	backend_storage_manager1 = tiletree.csvstorage.CSVStorageManager(open('meta_mt_mapserver_tree_1.csv','w'), open('meta_mt_mapserver_images_1.csv', 'w'))
	storage_manager1 = tiletree.splitstorage.SplitStorageManager(backend_storage_manager1, 3)

	backend_storage_manager2 = tiletree.csvstorage.CSVStorageManager(open('meta_mt_mapserver_tree_2.csv','w'), open('meta_mt_mapserver_images_2.csv', 'w'))
	storage_manager2 = tiletree.splitstorage.SplitStorageManager(backend_storage_manager2, 3)

	backend_storage_manager3 = tiletree.csvstorage.CSVStorageManager(open('meta_mt_mapserver_tree_3.csv','w'), open('meta_mt_mapserver_images_3.csv', 'w'))
	storage_manager3 = tiletree.splitstorage.SplitStorageManager(backend_storage_manager3, 3)

	jobs = []
	jobs.append( job_nodes[0].to_generator_job(storage_manager0,
			tiletree.mapserver.MapServerRenderer(open('split_default.map','r').read(),['poly_fill'], img_w=256, img_h=256),
			tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america'),
			stop_level) )
	jobs.append( job_nodes[1].to_generator_job(storage_manager1,
			tiletree.mapserver.MapServerRenderer(open('split_default.map','r').read(),['poly_fill'], img_w=256, img_h=256),
			tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america'),
			stop_level) )
	jobs.append( job_nodes[2].to_generator_job(storage_manager2,
			tiletree.mapserver.MapServerRenderer(open('split_default.map','r').read(),['poly_fill'], img_w=256, img_h=256),
			tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america'),
			stop_level) )
	jobs.append( job_nodes[3].to_generator_job(storage_manager3,
			tiletree.mapserver.MapServerRenderer(open('split_default.map','r').read(),['poly_fill'], img_w=256, img_h=256),
			tiletree.shapefile.ShapefileCutter('test_geo/webmerc_northamerica/north_america.shp', 'north_america'),
			stop_level) )

	tiletree.generate_mt(jobs, num_threads=4)

def postgres_csv_load_test():
	print "Postgres csv load test"
	storage_manager = tiletree.postgres.PostgresStorageManager('dbname=planetwoo user=planetwoo', 'tile_csv_nodes', 'tile_csv_images')
	storage_manager.recreate_tables()
	storage_manager.copy(open('mapserver_tree.csv','r'),open('mapserver_images.csv','r'))

def label_render_test():
	print "Label render test"
	feature_storage_manager = tiletree.postgres.PostgresStorageManager('dbname=planetwoo user=planetwoo', 'tile_csv_nodes', 'tile_csv_images')
	storage_manager = tiletree.fsstorage.FSStorageManager(image_prefix='test_images/')
	#storage_manager = tiletree.NullStorageManager()
	min_x, min_y, max_x, max_y = (-19338083.638408754, 804303.8439259261, -2215605.96243665, 17926781.51989803)
	renderer = tiletree.label.LabelRenderer(open('default.map','r').read(), feature_storage_manager)
	tiletree.generate(min_x, min_y, max_x, max_y, storage_manager, renderer, tiletree.NullGeomCutter(), stop_level=3)

def main():
	#null_test()
	#null_fs_tree_test()
	#null_csv_tree_test()
	#shapefile_cutter_test()
	##maptree_cutter_test()
	#mapserver_render_test()
	#postgres_test()
	##geom_builder_csv_test()
	##geom_builder_shapefile_test()
	##individual_geom_builder_shapefile_test()
	#meta_tile_mapserver_test()
	#mapserver_mt_test()
	#meta_mapserver_mt_test()
	#postgres_csv_load_test()
	label_render_test()

if( __name__ == '__main__'):
	main()

