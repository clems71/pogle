__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

class Stats(object):
	drawcalls = 0

	@staticmethod
	def clear():
		Stats.drawcalls = 0

	def __repr__(self):
		r = ''
		r += 'DRAWCALLS = %d\n' % Stats.drawcalls
		return r
		