import platform as pf
from glob import glob
import os

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

PLATFORM_UNKNOWN = 0
PLATFORM_MAC = 1
PLATFORM_WIN = 2
PLATFORM_LIN = 3

platform = PLATFORM_UNKNOWN

def _init():
	global platform

	os = pf.system().lower()
	if os == 'darwin':
		platform = PLATFORM_MAC
	elif os == 'windows':
		platform = PLATFORM_WIN
	elif os == 'linux':
		platform = PLATFORM_LIN

def findlib(libname, extrasearchpath=['./']):
	global platform

	extlst = []
	searchpath = extrasearchpath

	if platform == PLATFORM_MAC:
		extlst += ['.dylib', '.so']
		searchpath.append('/usr/local/lib')
	elif platform == PLATFORM_LIN:
		extlst += ['.so']
		searchpath.append('/usr/lib')

	for spath in searchpath:
		for ext in extlst:
			libs = glob(os.path.join(spath, '*%s*' % libname + ext))
			if len(libs) != 0:
				return libs[0]

_init()
