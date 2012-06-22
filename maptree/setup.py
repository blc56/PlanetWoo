from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import os

ext_modules = [
	Extension(
		"maptree",
		sources=["maptree.pyx",],
		language="c",
		include_dirs= os.environ.get('C_INCLUDE_PATH','').split(':'),
		library_dirs=os.environ.get('LIBRARY_PATH','').split(':'),
		libraries=["mapserver"],
		extra_compile_args=["-O0", "-g"],
	),
]

setup(
	name = "maptree",
	cmdclass = {"build_ext": build_ext},
	ext_modules = ext_modules,
)

