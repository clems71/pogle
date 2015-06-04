from ctypes import *

import OpenGL

from OpenGL.GL import *

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

# OpenGL Formats
GL_RG                  = 0x8227
GL_RG_INTEGER          = 0x8228
GL_R8                  = 0x8229
GL_R16                 = 0x822A
GL_RG8                 = 0x822B
GL_RG16                = 0x822C
GL_R16F                = 0x822D
GL_R32F                = 0x822E
GL_RG16F               = 0x822F
GL_RG32F               = 0x8230
GL_R8I                 = 0x8231
GL_R8UI                = 0x8232
GL_R16I                = 0x8233
GL_R16UI               = 0x8234
GL_R32I                = 0x8235
GL_R32UI               = 0x8236
GL_RG8I                = 0x8237
GL_RG8UI               = 0x8238
GL_RG16I               = 0x8239
GL_RG16UI              = 0x823A
GL_RG32I               = 0x823B
GL_RG32UI              = 0x823C

# PBO
GL_PIXEL_PACK_BUFFER   = 0x88EB
GL_PIXEL_UNPACK_BUFFER = 0x88EC

# Tessellation
GL_PATCH_VERTICES      = 0x8E72
# glPatchParameteri      = link_GL('glPatchParameteri', None, [GLenum, GLint], 'ARB_tessellation_shader')

# VAO
# glGenVertexArrays      = link_GL('glGenVertexArrays', None, [GLsizei, POINTER(GLuint)])
# glBindVertexArray      = link_GL('glBindVertexArray', None, [GLuint])

# Texture Buffers
GL_TEXTURE_BUFFER      = 0x8C2A
# glTexBuffer            = link_GL('glTexBuffer', None, [GLuint, GLuint, GLuint])