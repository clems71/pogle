import collections
from ctypes import *

from pogle_opengl import *

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

class BufferObject(object):
	_current = collections.defaultdict(lambda : None)

	def __init__(self, target, data_or_size, hint):
		self.target = target
		self.glid = glGenBuffers(1)
		self.bind()

		if type(data_or_size) == int:
			self.size = data_or_size
			glBufferData(self.target, data_or_size, None, hint)
		else:
			self.size = sizeof(data_or_size)
			glBufferData(self.target, sizeof(data_or_size), data_or_size, hint)

	def __del__(self):
		""" Delete the buffer object, unbind it and release associated resources
		"""
		BufferObject.unbind(self.target)
		glDeleteBuffers(1, byref(self.glid))

	@property
	def glname(self):
		return self.glid

	def bind(self):
		""" Bind this buffer object
		"""
		if BufferObject._current[self.target] != self:
			BufferObject._current[self.target] = self
			glBindBuffer(self.target, self.glid)

	def fill(self, data, off=0):
		""" Fill this buffer object with data
		"""
		self.bind()
		glBufferSubData(self.target, off, self.size, data)

	def map(self, mode):
		self.bind()
		if mode == 'r':
			return glMapBuffer(self.target, GL_READ_ONLY)
		elif mode == 'w':
			return glMapBuffer(self.target, GL_WRITE_ONLY)
		
		raise Exception('Invalid mode')

	def unmap(self):
		self.bind()
		glUnmapBuffer(self.target)

	@staticmethod
	def unbind(target):
		if BufferObject._current[target] != None:
			glBindBuffer(target, 0)
			BufferObject._current[target] = None

# class UniformBufferObject(BufferObject):
# 	def __init__(self, type_, count):
# 		self._client_mem_object = (type_ * count)()
# 		self._count = 0

# 		# Init the backing buffer
# 		super(UniformBufferObject, self).__init__(GL_UNIFORM_BUFFER, self._client_mem_object, GL_DYNAMIC_DRAW)
		
# 	def append(self, data):
# 		self._client_mem_object[self._count] = data
# 		self._count += 1
# 		self._changed = True

# 	def clear(self):
# 		self._count = 0
