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

##\file boundary_label.py Main classes for the tiletree.boundary_label module. 

import planetwoo.tiletree as tiletree
import tiletree.label as label

class BoundaryLabelRenderer(label.BaseLabelRenderer):
	def __init__(self, mapfile_string, label_col_index, mapserver_layers,
			min_zoom=0, max_zoom=100, label_spacing=1024, img_w=256, img_h=256, tile_buffer=256,
			info_cache_name=None):
		label.BaseLabelRenderer.__init__(self, img_w, img_h, info_cache_name)

	def tile_info(self, node, check_full=True):
		node.is_blank = False
		node.is_leaf = False
		node.is_full = False

