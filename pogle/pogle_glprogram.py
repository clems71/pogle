""" This module provides an easy to use interface to OpenGL shaders
"""
import xml.etree.ElementTree as ET
from string import Template
from ctypes import *
from cStringIO import StringIO

from pogle_gltexture import Texture1D, Texture2D, Texture3D, TextureBuffer
from pogle_math import Vector, Matrix4x4
from pogle_mesh import DefaultAttribStruct
from pogle_opengl import *

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

GL_GEOMETRY_SHADER = 0x8DD9
GL_TESS_CONTROL_SHADER = 0x8E88
GL_TESS_EVALUATION_SHADER = 0x8E87

UNIFORMS_DEFAULT = """
uniform mat4 viewMatrix;
uniform mat4 projMatrix;
uniform mat4 modelMatrix;

uniform vec3 lightPos;
"""

# Defines used across all shaders
VERTEX_SHADER_DEFINES = """

// Required on Mac OS X
#extension GL_ARB_explicit_attrib_location : enable

#define DEFINE_VAO_3D_DEFAULT \
	layout(location=0) in vec4 position; \
	layout(location=1) in vec3 normal; \
	layout(location=2) in vec3 tangent; \
	layout(location=3) in vec3 bitangent; \
	layout(location=4) in vec2 uv0;

#define DEFINE_VAO_2D_DEFAULT \
	layout(location=0) in vec4 position; \
	layout(location=1) in vec2 uv0;


"""

def _glUniformNf(idx, vec):
	if len(vec) == 2:
		glUniform2f(idx, vec.x, vec.y)
	elif len(vec) == 3:
		glUniform3f(idx, vec.x, vec.y, vec.z)
	elif len(vec) == 4:
		glUniform4f(idx, vec.x, vec.y, vec.z, vec.w)
	else:
		raise Exception('Unsupported Vector%d' % len(vec))

def _uniform_tex(idx, tex):
	tex.bind()
	glUniform1i(idx, tex.sampler_unit)

class GLProgram(object):
	""" Class to load OpenGL shaders
	"""
	UNIFORM_VTBL = {
		# list        : lambda idx, v: glUniform3fv(idx, len(v), ),
		int			   : lambda idx, v: glUniform1i(idx, v),
		Texture1D      : _uniform_tex,
		Texture2D      : _uniform_tex,
		Texture3D      : _uniform_tex,
		TextureBuffer  : _uniform_tex,
		float 		   : lambda idx, v: glUniform1f(idx, v),
		Vector 		   : lambda idx, v: _glUniformNf(idx, v),
		Matrix4x4 	   : lambda idx, v: glUniformMatrix4fv(idx, 1, GL_FALSE, v.data()),
	}


	def __init__(self, path=None, xml=None, defines=[], **kwargs):
		""" Create a shader from .shader file (XML syntax)

		defines -- A list of string containing user specified defines
		kwargs -- These params will be substituted in the shader (template shader)
		"""
		if xml != None:
			shader_filepath = StringIO(xml)
		else:
			shader_filepath = path

		tree = ET.parse(shader_filepath)
		root = tree.getroot()

		version = '#version %s\n' % root.attrib['version']

		defines = ''.join(['#define %s\n' % d for d in defines])

		uniforms_xml = root.find('uniforms')
		uniforms = version + VERTEX_SHADER_DEFINES + defines + UNIFORMS_DEFAULT
		if uniforms_xml != None:
			uniforms += uniforms_xml.text


		vert_src = uniforms + root.find('vertex').text
		frag_src = uniforms + root.find('fragment').text

		geom_src = root.find('geometry')
		if geom_src != None:
			geom_src = uniforms + geom_src.text

		tcs_src = root.find('tesscontrol')
		if tcs_src != None:
			tcs_src = uniforms + tcs_src.text

		tes_src = root.find('tesseval')
		if tes_src != None:
			tes_src = uniforms + tes_src.text

		# Shader templating
		if len(kwargs) != 0:
			vert_src = Template(vert_src).substitute(kwargs)
			frag_src = Template(frag_src).substitute(kwargs)
			if geom_src != None:
				geom_src = Template(geom_src).substitute(kwargs)
			if tcs_src != None:
				tcs_src = Template(tcs_src).substitute(kwargs)
			if tes_src != None:
				tes_src = Template(tes_src).substitute(kwargs)				

		self.prog = glCreateProgram()

		# Attach the vertex shader
		self.vert = GLProgram.__create_shader(vert_src, GL_VERTEX_SHADER)
		glAttachShader(self.prog, self.vert)

		# Attach the fragment shader
		self.frag = GLProgram.__create_shader(frag_src, GL_FRAGMENT_SHADER)
		glAttachShader(self.prog, self.frag)

		# Optional shaders
		self.geom = None
		self.tcs = None
		self.tes = None

		self.has_tessellation = False

		if geom_src != None:
			self.geom = GLProgram.__create_shader(geom_src, GL_GEOMETRY_SHADER)
			glAttachShader(self.prog, self.geom)
		if tcs_src != None:
			self.has_tessellation = True
			self.tcs = GLProgram.__create_shader(tcs_src, GL_TESS_CONTROL_SHADER)
			glAttachShader(self.prog, self.tcs)
		if tes_src != None:
			self.has_tessellation = True
			self.tes = GLProgram.__create_shader(tes_src, GL_TESS_EVALUATION_SHADER)
			glAttachShader(self.prog, self.tes)

		# Link
		glLinkProgram(self.prog)

		# And check it went right
		temp = glGetProgramiv(self.prog, GL_LINK_STATUS)
		if not temp:
			raise Exception(glGetProgramInfoLog(self.prog))

		self._uniforms_indices = {}
		

	def use(self):
		""" Mark the shader as active
		"""
		glUseProgram(self.prog)

	def set_uniform(self, name, value):
		if name not in self._uniforms_indices:
			idx = glGetUniformLocation(self.prog, name)
			self._uniforms_indices[name] = idx

		idx = self._uniforms_indices[name]
		if idx == -1:
			return
		GLProgram.UNIFORM_VTBL[type(value)](idx, value)

	@staticmethod
	def __create_shader(src, shader_type):
		shader_obj = glCreateShader(shader_type)
		glShaderSource(shader_obj, src)
		glCompileShader(shader_obj)

		result = glGetShaderiv(shader_obj, GL_COMPILE_STATUS)
		if not result:
			raise Exception(glGetShaderInfoLog(shader_obj))
			
		return shader_obj
