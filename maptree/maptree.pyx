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
	#cdef treeObj* msReadTree(char *filename, int debug)
	#cdef ms_bitarray msSearchTree(treeObj* tree, rectObj aio)

	cdef SHPTreeInfo* msSHPDiskTreeOpen(char *pszTree, int debug)
	cdef ms_bitarray msSearchDiskTree(char *filename, rectObj aoi, int debug)

#cdef class SHPTree:
class SHPTree:
	#cdef treeObj* tree
	#cdef SHPTreeInfo *tree


	def __init__(self, qix_file_path):
		#self.tree = msReadTree(qix_file_path, 0)
		#tree = msSHPDiskTreeOpen(file_path, 0)
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

