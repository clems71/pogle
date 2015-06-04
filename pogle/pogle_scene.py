from pogle_math import Vector, Matrix4x4, Transform

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

class Light(object):
	def __init__(self, pos=Vector(0.0, 0.0, 0.0)):
		self.position = pos

class Camera(object):
	def __init__(self, proj=None, view=None):
		if proj is None:
			proj = Matrix4x4()
		self.proj = proj
		if view is None:
			view = Matrix4x4()
		self.view = view
		self._follow_viewport = False

	def lookat(self, eye, center=Vector(0, 0, 0), up=Vector(0, 1, 0)):
		self.view = Matrix4x4.lookat(eye, center, up)

	@staticmethod
	def perspective(fovy, near, far):
		cam = Camera(Matrix4x4.perspective(fovy, 1.0, near, far))
		cam._near = near
		cam._fovy = fovy
		cam._far = far
		cam._follow_viewport = True
		return cam

	@staticmethod
	def ortho(near, far, width, height):
		return Camera(Matrix4x4.ortho(near, far, width, height))

class Scene(object):
	""" A scene is a container for all your objects.

	Basically, it contains a root node to be rendered, a camera and 
	0 to 3 directional lights.
	"""
	def __init__(self, camera=None):
		if camera is None:
			camera = Camera()

		self.passes = []
		self.camera = camera
		self.lights = []
		self._nodes = []

	def register_pass(self, pass_):
		assert pass_ not in self.passes
		self.passes.append(pass_)

	def unregister_pass(self, pass_):
		assert pass_ in self.passes
		self.passes.remove(pass_)

	def add_node(self, node):
		assert node.scene == None, 'The node is already attached to a scene'
		
		self._nodes.append(node)
		node.scene = self
		self.mark_renderlist_as_dirty()

	def mark_renderlist_as_dirty(self):
		for p in self.passes:
			p.mark_renderlist_as_dirty()

	def remove_node(self, node):
		assert node.scene == self, 'The node is not attached to this scene'

		self._nodes.remove(node)
		node.scene = None
		self.mark_renderlist_as_dirty()


	def add_light(self, light):
		self.lights.append(light)

	def get_nodes(self, flag):
		""" A method returning a list of all nodes having the flag 'flag'

		flag -- The flag that must be present on all nodes returned
		"""
		match = []
		for n in self._nodes:
			if n.has_flag(flag):
				match.append(n)
		return match

	def get_nodes_i(self, flag):
		""" A generator method returning all nodes having the flag 'flag'

		flag -- The flag that must be present on all nodes returned
		"""
		for n in self._nodes:
			if n.has_flag(flag):
				yield n

	def __len__(self):
		return len(self._nodes)

	@property
	def nodes(self):
		return self._nodes

class SceneNode(object):
	NODE_HAS_GEOMETRY = 1

	""" A basic base class for all node types
	"""
	def __init__(self, transform=None, flags=0x00000000):
		self.name = ''
		self.flags = flags

		# Trick to avoid the one default arg instanciation for all
		# If the default arg == Tranform(), every node which doesn't
		# specify the transform arg, will use the shared object created
		# on file parsing! Not what we want here.
		if transform is None:
			transform = Transform()

		self.transform = transform
		self.scene = None

	def has_flag(self, flag):
		return (self.flags & flag) != 0
