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

from libc.stdint cimport uint32_t, int32_t
from cython.operator cimport dereference as dref

cdef extern from "mapserver.h":
	ctypedef uint32_t *ms_bitarray

	#ctypedef struct treeObj:
		#int32_t numshapes
		#int32_t maxdepth

	ctypedef struct SHPTreeInfo:
		int32_t nShapes
		int32_t nDepth

	ctypedef struct rectObj:
		double minx
		double miny
		double maxx
		double maxy

	cdef int msGetBit(ms_bitarray array, int index)
	#NOTE: I'd prefer these functions, but they seem to be broken
	#cdef treeObj* msReadTree(char *filename, int debug)
	#cdef ms_bitarray msSearchTree(treeObj* tree, rectObj aio)

	cdef SHPTreeInfo* msSHPDiskTreeOpen(char *pszTree, int debug)
	cdef ms_bitarray msSearchDiskTree(char *filename, rectObj aoi, int debug)

#cdef class SHPTree:
class SHPTree:

	def __init__(self, qix_file_path):
		self.tree_path = qix_file_path
		cdef SHPTreeInfo* tree_handle = msSHPDiskTreeOpen(self.tree_path, 0)
		self.num_shapes = dref(tree_handle).nShapes
		self.depth = dref(tree_handle).nDepth

	def find_shapes(self, min_x, min_y, max_x, max_y):
		cdef rectObj rect
		cdef int32_t pos
		cdef ms_bitarray bit_results

		rect.minx = min_x
		rect.miny = min_y
		rect.maxx = max_x
		rect.maxy = max_y

		#bit_results = msSearchTree(self.tree, rect)
		bit_results = msSearchDiskTree(self.tree_path, rect, 0)

		contained_fids = []

		for pos in range(0, self.num_shapes):
			if(msGetBit(bit_results, pos) != 0):
				contained_fids.append(int(pos))

		return contained_fids

