import math
from ctypes import *

cimport cython
from cython cimport view

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

class Vector(object):
	def __init__(self, *args):
		self.vals = [float(f) for f in args]

	@property
	def x(self):
		return self.vals[0]
	@x.setter
	def x(self, val):
		self.vals[0] = val

	@property
	def y(self):
		return self.vals[1]
	@y.setter
	def y(self, val):
		self.vals[1] = val

	@property
	def z(self):
		return self.vals[2]
	@z.setter
	def z(self, val):
		self.vals[2] = val

	@property
	def w(self):
		return self.vals[3]
	@w.setter
	def w(self, val):
		self.vals[3] = val

	def __imul__(self, f):
		self.vals = [v * f for v in self.vals]

	def __mul__(self, f):
		return Vector(*[v * f for v in self.vals])

	def __idiv__(self, f):
		self.vals = [v / f for v in self.vals]

	def __sub__(self, vec):
		return Vector(*[a - b for a, b in zip(self.vals, vec.vals)])

	def __add__(self, vec):
		return Vector(*[a + b for a, b in zip(self.vals, vec.vals)])

	def cross(self, vec):
		assert len(self) == 3
		assert len(vec) == 3
		return Vector(
			self.y * vec.z - self.z * vec.y,
			self.z * vec.x - self.x * vec.z,
			self.x * vec.y - self.y * vec.x,
			)

	def abs(self):
		accum = 0.0
		for v in self.vals:
			accum += v * v
		return math.sqrt(accum)

	def dot(self, other):
		accum = 0.0
		for v1, v2 in zip(self.vals, other.vals):
			accum += v1 * v2
		return accum

	def abs2(self):
		accum = 0.0
		for v in self.vals:
			accum += v * v
		return accum

	def negated(self):
		return Vector(*[-a for a in self.vals])

	def normalize(self):
		self /= self.abs()

	def __len__(self):
		return len(self.vals)

	def __repr__(self):
		s = 'Vector%d(' % len(self)
		for v in self.vals:
			s += '%.3f, ' % v
		return s + ')'

class Rect(object):
	def __init__(self, x, y, width, height):
		self.x = x
		self.x = y
		self.width = width
		self.height = height


class AABB(object):
	def __init__(self, mn, mx):
		self.min = mn
		self.max = mx

	def to_bounding_sphere(self):
		center = (self.max + self.min) * 0.5
		radii = ((self.max - self.min) * 0.5).abs()
		return Sphere(center, radii)

class Sphere(object):
	def __init__(self, center, radii):
		self.center = center
		self.radii = radii

float_ptr_t = POINTER(c_float)

def _matrix44_unpickle():
	return Matrix4x4()

@cython.final
cdef class Matrix4x4(object):
	cdef float[16] vals
	cdef public int is_identity

	def __init__(self):
		self.vals[0] = 1.0 ; self.vals[4] = 0.0 ; self.vals[8 ] = 0.0 ; self.vals[12] = 0.0
		self.vals[1] = 0.0 ; self.vals[5] = 1.0 ; self.vals[9 ] = 0.0 ; self.vals[13] = 0.0
		self.vals[2] = 0.0 ; self.vals[6] = 0.0 ; self.vals[10] = 1.0 ; self.vals[14] = 0.0
		self.vals[3] = 0.0 ; self.vals[7] = 0.0 ; self.vals[11] = 0.0 ; self.vals[15] = 1.0
		self.is_identity = 1
	
	cpdef float get(self, int x, int y):
		return self.vals[y + x * 4]

	cpdef set(self, int x, int y, float val):
		self.vals[y + x * 4] = val

	def data(self):
		p_vals = <float *>self.vals
		return cast(<long>p_vals, float_ptr_t)

	def __setstate__(self, data):
		self.is_identity = 0
		i = 0
		for f in data['vals']:
			self.vals[i] = f
			i += 1

	def __reduce__(self):
		return (_matrix44_unpickle, (), {'vals' : [float(f) for f in self.vals]})
		# data = ''
		# for f in self.vals:
		# 	f = float(f)
		# 	data += '%f!' % f
		# return data

	cpdef inverse(self):
		cdef float[16] inv
		cdef float det
		cdef int i

		inv[0] = self.vals[5]  * self.vals[10] * self.vals[15] - \
				 self.vals[5]  * self.vals[11] * self.vals[14] - \
				 self.vals[9]  * self.vals[6]  * self.vals[15] + \
				 self.vals[9]  * self.vals[7]  * self.vals[14] + \
				 self.vals[13] * self.vals[6]  * self.vals[11] - \
				 self.vals[13] * self.vals[7]  * self.vals[10]

		inv[4] = -self.vals[4]  * self.vals[10] * self.vals[15] + \
				  self.vals[4]  * self.vals[11] * self.vals[14] + \
				  self.vals[8]  * self.vals[6]  * self.vals[15] - \
				  self.vals[8]  * self.vals[7]  * self.vals[14] - \
				  self.vals[12] * self.vals[6]  * self.vals[11] + \
				  self.vals[12] * self.vals[7]  * self.vals[10]

		inv[8] = self.vals[4]  * self.vals[9] * self.vals[15] - \
				 self.vals[4]  * self.vals[11] * self.vals[13] - \
				 self.vals[8]  * self.vals[5] * self.vals[15] + \
				 self.vals[8]  * self.vals[7] * self.vals[13] + \
				 self.vals[12] * self.vals[5] * self.vals[11] - \
				 self.vals[12] * self.vals[7] * self.vals[9]

		inv[12] = -self.vals[4]  * self.vals[9] * self.vals[14] + \
				   self.vals[4]  * self.vals[10] * self.vals[13] +\
				   self.vals[8]  * self.vals[5] * self.vals[14] - \
				   self.vals[8]  * self.vals[6] * self.vals[13] - \
				   self.vals[12] * self.vals[5] * self.vals[10] + \
				   self.vals[12] * self.vals[6] * self.vals[9]

		inv[1] = -self.vals[1]  * self.vals[10] * self.vals[15] + \
				  self.vals[1]  * self.vals[11] * self.vals[14] + \
				  self.vals[9]  * self.vals[2] * self.vals[15] - \
				  self.vals[9]  * self.vals[3] * self.vals[14] - \
				  self.vals[13] * self.vals[2] * self.vals[11] + \
				  self.vals[13] * self.vals[3] * self.vals[10]

		inv[5] = self.vals[0]  * self.vals[10] * self.vals[15] - \
				 self.vals[0]  * self.vals[11] * self.vals[14] - \
				 self.vals[8]  * self.vals[2] * self.vals[15] + \
				 self.vals[8]  * self.vals[3] * self.vals[14] + \
				 self.vals[12] * self.vals[2] * self.vals[11] - \
				 self.vals[12] * self.vals[3] * self.vals[10]

		inv[9] = -self.vals[0]  * self.vals[9] * self.vals[15] + \
				  self.vals[0]  * self.vals[11] * self.vals[13] + \
				  self.vals[8]  * self.vals[1] * self.vals[15] - \
				  self.vals[8]  * self.vals[3] * self.vals[13] - \
				  self.vals[12] * self.vals[1] * self.vals[11] + \
				  self.vals[12] * self.vals[3] * self.vals[9]

		inv[13] = self.vals[0]  * self.vals[9] * self.vals[14] - \
				  self.vals[0]  * self.vals[10] * self.vals[13] - \
				  self.vals[8]  * self.vals[1] * self.vals[14] + \
				  self.vals[8]  * self.vals[2] * self.vals[13] + \
				  self.vals[12] * self.vals[1] * self.vals[10] - \
				  self.vals[12] * self.vals[2] * self.vals[9]

		inv[2] = self.vals[1]  * self.vals[6] * self.vals[15] - \
				 self.vals[1]  * self.vals[7] * self.vals[14] - \
				 self.vals[5]  * self.vals[2] * self.vals[15] + \
				 self.vals[5]  * self.vals[3] * self.vals[14] + \
				 self.vals[13] * self.vals[2] * self.vals[7] - \
				 self.vals[13] * self.vals[3] * self.vals[6]

		inv[6] = -self.vals[0]  * self.vals[6] * self.vals[15] + \
				  self.vals[0]  * self.vals[7] * self.vals[14] + \
				  self.vals[4]  * self.vals[2] * self.vals[15] - \
				  self.vals[4]  * self.vals[3] * self.vals[14] - \
				  self.vals[12] * self.vals[2] * self.vals[7] + \
				  self.vals[12] * self.vals[3] * self.vals[6]

		inv[10] = self.vals[0]  * self.vals[5] * self.vals[15] - \
				  self.vals[0]  * self.vals[7] * self.vals[13] - \
				  self.vals[4]  * self.vals[1] * self.vals[15] + \
				  self.vals[4]  * self.vals[3] * self.vals[13] + \
				  self.vals[12] * self.vals[1] * self.vals[7] - \
				  self.vals[12] * self.vals[3] * self.vals[5]

		inv[14] = -self.vals[0]  * self.vals[5] * self.vals[14] + \
				   self.vals[0]  * self.vals[6] * self.vals[13] + \
				   self.vals[4]  * self.vals[1] * self.vals[14] - \
				   self.vals[4]  * self.vals[2] * self.vals[13] - \
				   self.vals[12] * self.vals[1] * self.vals[6] + \
				   self.vals[12] * self.vals[2] * self.vals[5]

		inv[3] = -self.vals[1] * self.vals[6] * self.vals[11] + \
				  self.vals[1] * self.vals[7] * self.vals[10] + \
				  self.vals[5] * self.vals[2] * self.vals[11] - \
				  self.vals[5] * self.vals[3] * self.vals[10] - \
				  self.vals[9] * self.vals[2] * self.vals[7] + \
				  self.vals[9] * self.vals[3] * self.vals[6]

		inv[7] = self.vals[0] * self.vals[6] * self.vals[11] - \
				 self.vals[0] * self.vals[7] * self.vals[10] - \
				 self.vals[4] * self.vals[2] * self.vals[11] + \
				 self.vals[4] * self.vals[3] * self.vals[10] + \
				 self.vals[8] * self.vals[2] * self.vals[7] - \
				 self.vals[8] * self.vals[3] * self.vals[6]

		inv[11] = -self.vals[0] * self.vals[5] * self.vals[11] + \
				   self.vals[0] * self.vals[7] * self.vals[9] + \
				   self.vals[4] * self.vals[1] * self.vals[11] - \
				   self.vals[4] * self.vals[3] * self.vals[9] - \
				   self.vals[8] * self.vals[1] * self.vals[7] + \
				   self.vals[8] * self.vals[3] * self.vals[5]

		inv[15] = self.vals[0] * self.vals[5] * self.vals[10] - \
				  self.vals[0] * self.vals[6] * self.vals[9] - \
				  self.vals[4] * self.vals[1] * self.vals[10] + \
				  self.vals[4] * self.vals[2] * self.vals[9] + \
				  self.vals[8] * self.vals[1] * self.vals[6] - \
				  self.vals[8] * self.vals[2] * self.vals[5]

		det = self.vals[0] * inv[0] + self.vals[1] * inv[4] + \
				self.vals[2] * inv[8] + self.vals[3] * inv[12]

		if det == 0:
			return None

		det = 1.0 / det;
		res = Matrix4x4()
		res.is_identity = self.is_identity
		for i in range(16):
			res.vals[i] = inv[i] * det;
		return res

	@staticmethod
	def lookat(eye, center, up=Vector(0, 1, 0)):
		res = Matrix4x4()
		forward = center - eye
		forward.normalize()

		side = forward.cross(up)
		side.normalize()

		up = side.cross(forward)

		res.set(0, 0, side.x)
		res.set(1, 0, side.y)
		res.set(2, 0, side.z)

		res.set(0, 1, up.x)
		res.set(1, 1, up.y)
		res.set(2, 1, up.z)

		res.set(0, 2, -forward.x)
		res.set(1, 2, -forward.y)
		res.set(2, 2, -forward.z)
		
		res.is_identity = 0

		res = res * Matrix4x4.translation(eye.negated())
		return res

	@staticmethod
	def frustum(near, far, width, height):
		cdef Matrix4x4 res = Matrix4x4()

		res.vals[0]  = 2.0 * near / width
		res.vals[5]  = 2.0 * near / height
		res.vals[10] = -(far + near) / (far - near)
		res.vals[14] = -2.0 * far * near / (far - near)
		res.vals[11] = -1.0
		res.vals[15] = 0.0

		res.is_identity = 0

		return res

	@staticmethod
	def perspective(fovy, aspect, near, far):
		height = math.tan( fovy * math.pi / 360.0 ) * near * 2.0
		width = height * aspect
		return Matrix4x4.frustum(near, far, width, height)

	@staticmethod
	def ortho(near, far, width, height):
		res = Matrix4x4()
		res.set(0, 0, 2.0 / width)
		res.set(1, 1, 2.0 / height)
		res.set(2, 2, -2.0 / (far - near))
		res.set(3, 2, -(far + near) / (far - near))
		res.is_identity = 0
		return res

	@staticmethod
	def rotation(vec3):
		x_rot = Matrix4x4()
		x_rot.set(1, 1, math.cos(vec3.x))
		x_rot.set(2, 1, -math.sin(vec3.x))
		x_rot.set(1, 2, math.sin(vec3.x))
		x_rot.set(2, 2, math.cos(vec3.x))
		x_rot.is_identity = 0

		y_rot = Matrix4x4()
		y_rot.set(0, 0, math.cos(vec3.y))
		y_rot.set(2, 0, math.sin(vec3.y))
		y_rot.set(0, 2, -math.sin(vec3.y))
		y_rot.set(2, 2, math.cos(vec3.y))
		y_rot.is_identity = 0

		z_rot = Matrix4x4()
		z_rot.set(0, 0, math.cos(vec3.z))
		z_rot.set(1, 0, -math.sin(vec3.z))
		z_rot.set(0, 1, math.sin(vec3.z))
		z_rot.set(1, 1, math.cos(vec3.z))
		z_rot.is_identity = 0

		return x_rot * y_rot * z_rot

	@staticmethod
	def translation(vec3):
		res = Matrix4x4()
		res.vals[12] = vec3.x
		res.vals[13] = vec3.y
		res.vals[14] = vec3.z
		res.is_identity = 0
		return res

	@staticmethod
	def scale(vec3):
		res = Matrix4x4()
		res.vals[0] = vec3.x
		res.vals[5] = vec3.y
		res.vals[10] = vec3.z
		res.is_identity = 0
		return res

	def __repr__(self):
		r = ''
		for y in range(4):
			for x in range(4):
				r += '%f, ' % self.get(x, y)
		return r

	def __mul__(self, other):
		cdef int i
		cdef int x
		cdef int y
		cdef float s

		if other.is_identity == 1:
			return self
		elif self.is_identity == 1:
			return other
		elif type(other) == Matrix4x4:
			result = Matrix4x4()
			result.is_identity = 0
			for x in range(4):
				for y in range(4):
					s = 0.0
					for i in range(4):
						s += self.get(i, y) * other.get(x, i)
					result.set(x, y, s)

			return result
		else:
			raise Exception('Cannot multiply Matrix4x4 with %s' % repr(type(other)))

class Transform(object):
	""" A transform object, that enable parenting (hierarchy)
	"""
	def __init__(self, mat=Matrix4x4()):
		self._children = set()
		self._matrix = mat
		self._mulmat = mat
		self._parentmat = Matrix4x4()

	def _update(self):
		""" Recompute needed matrices to suit the latest changes
		"""
		self._mulmat = self._parentmat * self._matrix
		for childtf in self._children:
			childtf._parentmat = self._mulmat
			childtf._update()

	def add_child(self, childtf):
		self._children.add(childtf)
		childtf._parentmat = self._mulmat
		childtf._update()

	def remove_child(self, childtf):
		assert childtf in self._children
		childtf._parentmat = Matrix4x4()
		childtf._update()

	@property
	def matrix(self):
		return self._matrix

	@matrix.setter
	def matrix(self, value):
		self._matrix = value
		self._update()

	@property
	def premul_matrix(self):
		""" This is the matrix taking into account the whole hierarchy
		"""
		return self._mulmat
