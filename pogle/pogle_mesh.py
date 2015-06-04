# Asset import : Assimp library
# from pyassimp import pyassimp

from ctypes import *
import cPickle
import logging

from pogle_math import Matrix4x4, AABB, Vector, Transform
from pogle_scene import SceneNode
from pogle_bufferobject import BufferObject
from pogle_opengl import *
from pogle_stats import Stats

import pyassimp

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

# Not defined in base library
GL_PATCHES = 0x000E


class Vec2(Structure):
    _fields_ = [
        ('x', GLfloat),
        ('y', GLfloat),
    ]

    _attribs_ = [
        (2, GL_FLOAT, GL_FALSE),
    ]


class Vec3(Structure):
    _fields_ = [
        ('x', GLfloat),
        ('y', GLfloat),
        ('z', GLfloat),
    ]


class DefaultAttribStruct(Structure):
    """ Describe per-vertex data (attributes in OpenGL terms)
	"""
    _fields_ = [
        ('position', Vec3),
        ('normal', Vec3),
        ('tangent', Vec3),
        ('bitangent', Vec3),
        ('uv0', Vec2),
    ]

    _attribs_ = [
        (3, GL_FLOAT, GL_FALSE ),
        (3, GL_FLOAT, GL_TRUE  ),
        (3, GL_FLOAT, GL_TRUE  ),
        (3, GL_FLOAT, GL_TRUE  ),
        (2, GL_FLOAT, GL_FALSE ),
    ]


class AttribStruct2D(Structure):
    """ Describe per-vertex data (attributes in OpenGL terms)
	"""
    _fields_ = [
        ('position', Vec2),
        ('uv0', Vec2),
    ]

    _attribs_ = [
        (2, GL_FLOAT, GL_FALSE),
        (2, GL_FLOAT, GL_FALSE),
    ]


class GeometryNode(SceneNode):
    def __init__(self, geom, transform=None, material=None):
        super(GeometryNode, self).__init__(transform, SceneNode.NODE_HAS_GEOMETRY)

        self.geom = geom

        # Default engine material
        self._material = None

        self.material = material

    @property
    def material(self):
        return self._material

    @material.setter
    def material(self, val):
        if self._material != val:
            self._material = val
            if self.scene != None:
                self.scene.mark_renderlist_as_dirty()

    def render(self, renderer):
        self.geom.draw(renderer)

    @staticmethod
    def load_from_file(path):
        return GeometryNode(Geometry.load_from_file(path))


class VAO(object):
    _current = None

    def __init__(self):
        self.glid = glGenVertexArrays(1)
        self.bind()

    def bind(self):
        """ Bind this VAO
		"""
        if VAO._current != self:
            VAO._current = self
            glBindVertexArray(self.glid)

    @staticmethod
    def unbind():
        glBindVertexArray(0)
        VAO._current = None


class DynamicGeomRef(object):
    def __init__(self, other, mode):
        self.root = other
        self.drawmode = mode

    def draw(self, renderer):
        self.root.draw(renderer, self.drawmode)


class DynamicGeom(object):
    def __init__(self, attrib_type, count, mode=GL_LINE_STRIP):
        """
		attrib_type -- A Structure inherited type defining per vertex attribs
		"""
        self._changed = False
        self._count = 0
        self.drawmode = mode
        self.vao = VAO()
        self.vbo = BufferObject(GL_ARRAY_BUFFER, sizeof(attrib_type) * count, GL_DYNAMIC_DRAW)
        self._client_mem_object = (attrib_type * count)()

        attrib_type_size = sizeof(attrib_type)
        attrib_id = 0
        offset = 0
        for details in attrib_type._attribs_:
            glEnableVertexAttribArray(attrib_id)
            attrib_size = details[0]
            attrib_gltype = details[1]
            attrib_normalized = details[2]
            glVertexAttribPointer(attrib_id, attrib_size, attrib_gltype, attrib_normalized, attrib_type_size, offset)
            attrib_id += 1
            print('')
            print('>>>> WARNING : Get real size instead of assuming 32 bits')
            print('')
            offset += 4 * attrib_size

    def append(self, data):
        self._client_mem_object[self._count] = data
        self._count += 1
        self._changed = True

    def __getitem__(self, idx):
        return self._client_mem_object[idx]

    def __setitem__(self, idx, val):
        self._client_mem_object[idx] = val

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, val):
        self._count = val
        self._changed = True

    def clear(self):
        self._count = 0

    def draw(self, renderer, mode=None):
        self.vao.bind()

        if self._changed:
            self.vbo.fill(self._client_mem_object)
            self._changed = False

        mode = self.drawmode if mode is None else mode
        glDrawArrays(mode, 0, self._count)

        Stats.drawcalls += 1


class Geometry(object):
    """ Raw geometry, with no transform applied on it
	"""

    def __init__(self, attribs, indices, aabb=None):
        attrib_type = type(attribs[0])
        attrib_type_size = sizeof(attrib_type)

        self.aabb = aabb

        self.idx_count = len(indices)
        self.tri_count = self.idx_count / 3

        # Create a container for all Buffer Objects
        self.vao = VAO()

        # Mesh Buffer Objects
        self.indices_vbo = BufferObject(GL_ELEMENT_ARRAY_BUFFER, indices, GL_STATIC_DRAW)
        self.vbo = BufferObject(GL_ARRAY_BUFFER, attribs, GL_STATIC_DRAW)

        attrib_id = 0
        for attrib, details in zip(attrib_type._fields_, attrib_type._attribs_):
            glEnableVertexAttribArray(attrib_id)
            attrib_name = attrib[0]
            attrib_size = details[0]
            attrib_gltype = details[1]
            attrib_normalized = details[2]
            glVertexAttribPointer(attrib_id, attrib_size, attrib_gltype, attrib_normalized, attrib_type_size,
                                  ctypes.c_void_p(getattr(attrib_type, attrib_name).offset))
            attrib_id += 1

        # VAO.unbind()

    def draw(self, renderer):
        self.vao.bind()

        # If tessellation is enabled, it has to be rendered as patch
        if renderer.current_material._shader.has_tessellation:
            glDrawElements(GL_PATCHES, self.idx_count, GL_UNSIGNED_INT, None)
        # Else, as simple triangles
        else:
            glDrawElements(GL_TRIANGLES, self.idx_count, GL_UNSIGNED_INT, None)

        Stats.drawcalls += 1

    @staticmethod
    def load_from_file(path):
        path_cache = path + '.geomcache'

        try:
            fcache = open(path_cache, 'rb')
            attribs_bytes, indices_bytes, aabb_min, aabb_max, numverts, numtris = cPickle.load(fcache)
            attribs = (DefaultAttribStruct * numverts).from_buffer(attribs_bytes)
            indices = (GLuint * numtris).from_buffer(indices_bytes)
            aabb_min = Vector(*aabb_min)
            aabb_max = Vector(*aabb_max)
            return Geometry(attribs, indices, AABB(aabb_min, aabb_max))
        except :
            logging.warn('Failed to load geometry ' + path + ' from cache')

        scene = pyassimp.load(path, pyassimp.postprocess.aiProcessPreset_TargetRealtime_Quality)
        mesh = scene.meshes[0]

        if len(mesh.vertices) == 0:
            return None

        attribs = (DefaultAttribStruct * len(mesh.vertices))()
        indices = (GLuint * (len(mesh.faces) * 3))()

        # UV layers
        uv0 = (0.0, 0.0)
        uvlayers = 0

        if mesh.numuvcomponents[0] >= 2:
            uvlayers += 1

        v0 = mesh.vertices[0]
        aabb_min = Vector(v0[0], v0[1], v0[2])
        aabb_max = Vector(v0[0], v0[1], v0[2])

        # Fill attributes
        for idx in range(len(mesh.vertices)):
            vertex = mesh.vertices[idx]
            normal = mesh.normals[idx]
            tangent = mesh.tangents[idx]
            bitangent = mesh.bitangents[idx]

            if uvlayers != 0:
                uv0 = mesh.texturecoords[0][idx]

            # Build the AABB
            if vertex[0] < aabb_min.x:
                aabb_min.x = vertex[0]
            if vertex[1] < aabb_min.y:
                aabb_min.y = vertex[1]
            if vertex[2] < aabb_min.z:
                aabb_min.z = vertex[2]
            if vertex[0] > aabb_max.x:
                aabb_max.x = vertex[0]
            if vertex[1] > aabb_max.y:
                aabb_max.y = vertex[1]
            if vertex[2] > aabb_max.z:
                aabb_max.z = vertex[2]

            attribs[idx].position.x = vertex[0]
            attribs[idx].position.y = vertex[1]
            attribs[idx].position.z = vertex[2]

            attribs[idx].normal.x = normal[0]
            attribs[idx].normal.y = normal[1]
            attribs[idx].normal.z = normal[2]

            attribs[idx].tangent.x = tangent[0]
            attribs[idx].tangent.y = tangent[1]
            attribs[idx].tangent.z = tangent[2]

            attribs[idx].bitangent.x = bitangent[0]
            attribs[idx].bitangent.y = bitangent[1]
            attribs[idx].bitangent.z = bitangent[2]

            attribs[idx].uv0.x = uv0[0]
            attribs[idx].uv0.y = uv0[1]

        # Create indices array
        for idx, f in enumerate(mesh.faces):
            assert len(f) == 3
            indices[idx * 3 + 0] = f[0]
            indices[idx * 3 + 1] = f[1]
            indices[idx * 3 + 2] = f[2]

        with open(path_cache, 'wb') as fcache:
            geom_cache = (bytearray(attribs), bytearray(indices), aabb_min.vals, aabb_max.vals, len(mesh.vertices), len(mesh.faces)*3, )
            cPickle.dump(geom_cache, fcache, -1)

        return Geometry(attribs, indices, AABB(aabb_min, aabb_max))


class FullScreenQuad(Geometry):
    def __init__(self):
        attribs = (AttribStruct2D * 4)()
        attribs[0].position = Vec2(x=-1, y=-1)
        attribs[1].position = Vec2(x=1, y=-1)
        attribs[2].position = Vec2(x=1, y=1)
        attribs[3].position = Vec2(x=-1, y=1)

        attribs[0].uv0 = Vec2(x=0, y=0)
        attribs[1].uv0 = Vec2(x=1, y=0)
        attribs[2].uv0 = Vec2(x=1, y=1)
        attribs[3].uv0 = Vec2(x=0, y=1)

        indices = (GLuint * 6)(0, 1, 3, 3, 1, 2)
        super(FullScreenQuad, self).__init__(attribs, indices)
