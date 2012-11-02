import json
import psycopg2

from planetwoo.tiletree import load_cutter, load_renderer
import planetwoo.tiletree.mapserver as mapserver
import planetwoo.tiletree.label as label
import planetwoo.tiletree.postgres as postgres
import planetwoo.tiletree.composite as composite
import planetwoo.tiletree.memcached as memcached

def load_config(config_path, conn_str, force_create, recreate_layers, memcache):
	config = json.loads(open(config_path, 'r').read())
	render_infos = {}

	postgres_conn = psycopg2.connect(conn_str)

	for layer_name in config['layer_order']:
		layer = config['layers'][layer_name]
		#apply the dynamic override settings
		layer.update(layer.get('dynamic_override', {}))
		cutter = load_cutter(layer)
		renderer = load_renderer(layer)

		#have all of the storage_managers use the same connection so we don't overwhelm postgres
		storage_manager = postgres.PostgresStorageManager(None, layer['tree_table'],
			layer['image_table'], postgres_conn)
		render_infos[layer_name] = composite.RenderInfo(layer_name, storage_manager, renderer, cutter,
			layer.get('check_full', True), layer.get('min_zoom', None), layer.get('max_zoom', None))

		if(layer.get('renderer_type', '') == 'label'):
			renderer.storage_manager = storage_manager

		if(force_create or layer_name in recreate_layers or not storage_manager.do_tables_exist()):
			print 'Recreating', storage_manager.node_table, storage_manager.image_table
			storage_manager.recreate_tables()

		compositor = composite.TileCompositor(render_infos, config['layer_order'], config['map_extent'])
		if(memcache != None):
			compositor = memcached.MCDStorageManager(compositor, memcache, config['layer_order'])

	return (compositor, config['layer_groups'])

