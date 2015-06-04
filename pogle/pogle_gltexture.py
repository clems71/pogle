# Python Imaging Library : PIL
from PIL import Image

from ctypes import *
import cPickle
import logging
import weakref

import OpenEXR
import Imath
import numpy as np

from pogle_opengl import *
from pogle_bufferobject import BufferObject

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

GL_MAPPING = {
    'rgb'                   : (GL_RGB, GL_UNSIGNED_BYTE, GL_RGB, 3),
    'rgba'                  : (GL_RGBA, GL_UNSIGNED_BYTE, GL_RGBA, 4),
    'rgb16'                 : (GL_RGB, GL_UNSIGNED_SHORT, GL_RGB16, 6),
    'rgba16'                : (GL_RGBA, GL_UNSIGNED_SHORT, GL_RGBA16, 8),
    'rgb10a2'               : (GL_RGBA, GL_UNSIGNED_INT_10_10_10_2, GL_RGB10_A2, 4),
    'rgba32f'               : (GL_RGBA, GL_FLOAT, GL_RGBA32F, 16),

    'depth8'                : (GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, GL_DEPTH_COMPONENT, 1),
    'depth16'               : (GL_DEPTH_COMPONENT, GL_UNSIGNED_SHORT, GL_DEPTH_COMPONENT16, 2),

    'rg8'                   : (GL_RG, GL_UNSIGNED_BYTE, GL_RG, 2),
    'rg16'                  : (GL_RG, GL_UNSIGNED_SHORT, GL_RG16, 4),
    'rg32f'                 : (GL_RG, GL_FLOAT, GL_RG32F, 8),

    'r8'                    : (GL_RED, GL_UNSIGNED_BYTE, GL_RED, 1),
    'l8'                    : (GL_RED, GL_UNSIGNED_BYTE, GL_RED, 1),
    'r16'                   : (GL_RED, GL_UNSIGNED_SHORT, GL_R16, 2),
    'l16'                   : (GL_RED, GL_UNSIGNED_SHORT, GL_R16, 2),
    
    'r32f'                  : (GL_RED, GL_FLOAT, GL_R32F, 4),
}

FMT_PIL_MAPPING = {
    'rgb': 'RGB',
    'rgba': 'RGBA',
    'r8': 'L',
    'l8': 'L',
    'r32f': 'F',
}

TEX_UNIT_COUNT = 16

class TextureUnit(object):
    _bindings = {}
    _mru = []

    # At startup, all units are free
    _free_units = range(TEX_UNIT_COUNT)

    @staticmethod
    def bind(texref):
        if texref in TextureUnit._bindings:
            TextureUnit._mru.remove(texref)
        else:
            unit = -1

            if len(TextureUnit._free_units) > 0:
                unit = TextureUnit._free_units.pop()
            else:
                # No more texture unit is free
                # We have to free the oldest
                assert len(TextureUnit._mru) == TEX_UNIT_COUNT

                # Oldest one
                oldest_tex = TextureUnit._mru.pop()
                unit = TextureUnit._bindings[oldest_tex]
                del TextureUnit._bindings[oldest_tex]

            TextureUnit._bindings[texref] = unit
            texref()._bind(unit)

        # Place at the beginning, indicating it is recent
        TextureUnit._mru.insert(0, texref)

    @staticmethod
    def unbind(texref):
        if texref in TextureUnit._bindings:
            TextureUnit._mru.remove(texref)
            unit = TextureUnit._bindings[texref]
            del TextureUnit._bindings[texref]
            TextureUnit._free_units.append(unit)

class GLTexture(object):
    def __init__(self, target, format):
        assert type(self) != GLTexture, 'Cannot instantiate abstract class'

        self.fmtk = format
        self.fmt = GL_MAPPING[format]
        self.target = target

        self.wref = weakref.ref(self)

        self.texid = glGenTextures(1)
        self.bind()

    def _paramf(self, name, val):
        glTexParameterf(self.target, name, val)

    @property
    def format(self):
        return self.fmtk

    def __del__(self):
        glDeleteTextures([self.texid])
        glFlush()
        TextureUnit.unbind(self.wref)

    def _bind(self, unit):
        self.sampler_unit = unit
        self._enable_current_unit()
        glBindTexture(self.target, self.texid)

    def _enable_current_unit(self):
        glActiveTexture(GL_TEXTURE0 + self.sampler_unit)

    def bind(self):
        TextureUnit.bind(self.wref)


class TextureBuffer(GLTexture):
    def __init__(self, width, format='rgb'):
        super(TextureBuffer, self).__init__(GL_TEXTURE_BUFFER, format)
        self.width = width
        self.bufobj = BufferObject(GL_TEXTURE_BUFFER, width * self.fmt[3], GL_DYNAMIC_DRAW)
        glTexBuffer(GL_TEXTURE_BUFFER, self.fmt[2], self.bufobj.glname)

    def fill(self, data):
        """ Fill the texture buffer with some data
        """
        self.bufobj.fill(data)


class Texture1D(GLTexture):
    def __init__(self, data, width, format='rgb', filtering='linear'):
        """ Create an OpenGL texture 1D object from user data

        data -- a c_char_p object (can be None if an empty texture object has to be created)
        width -- texture width
        """
        super(Texture1D, self).__init__(GL_TEXTURE_1D, format)

        self.width = width
        self.bytesize = self.width * self.fmt[3]
        filtering = GL_LINEAR if filtering == 'linear' else GL_NEAREST

        self._paramf(GL_TEXTURE_WRAP_S, GL_REPEAT)
        self._paramf(GL_TEXTURE_MAG_FILTER, filtering)
        self._paramf(GL_TEXTURE_MIN_FILTER, filtering)

        # Set the data
        glTexImage1D(self.target, 0, self.fmt[2], width, 0, self.fmt[0], self.fmt[1], data)

    @staticmethod
    def from_image(path):
        img = Image.open(path)
        width, height = img.size
        assert height == 1, 'Texture1D has to be 1px high'
        fmt = img.mode
        data = img.convert('RGBA').tostring("raw", 'RGBA')
        return Texture1D(c_char_p(data), width, 'rgba')


class Texture2D(GLTexture):
    def __init__(self, data, width, height, format='rgb', filtering='linear', wrap=[GL_REPEAT, GL_REPEAT], mipmaps=False):
        """ Create an OpenGL texture 2D object from user data

        data -- a c_char_p object (can be None if an empty texture object has to be created)
        width -- texture width
        height -- texture height
        """
        super(Texture2D, self).__init__(GL_TEXTURE_2D, format)

        self.pbo = None
        self.pbo_dl = None
        self.width, self.height = width, height
        self.bytesize = self.width * self.height * self.fmt[3]
        filtering = GL_LINEAR if filtering == 'linear' else GL_NEAREST

        self._paramf(GL_TEXTURE_WRAP_S, wrap[0])
        self._paramf(GL_TEXTURE_WRAP_T, wrap[1])
        self._paramf(GL_TEXTURE_MAG_FILTER, filtering)

        if mipmaps and filtering == GL_LINEAR:
            filtering = GL_LINEAR_MIPMAP_LINEAR

        self._paramf(GL_TEXTURE_MIN_FILTER, filtering)

        # Set the data
        glTexImage2D(self.target, 0, self.fmt[2], width, height, 0, self.fmt[0], self.fmt[1], data)
        if mipmaps:
            glGenerateMipmap(self.target)

    @staticmethod
    def from_image(path, mipmaps=False, wrap=[GL_REPEAT, GL_REPEAT]):
        path_cache = path + '.texcache'

        try:
            fcache = open(path_cache, 'rb')
            data, width, height, formatstring = cPickle.load(fcache)
            return Texture2D(data, width, height, formatstring, wrap=wrap, mipmaps=mipmaps)
        except:
            logging.warn('Failed to load texture ' + path + ' from cache')

        if path.endswith('.exr'):
            pt = Imath.PixelType(Imath.PixelType.FLOAT)
            f = OpenEXR.InputFile(path)
            chan_r = np.fromstring(f.channel('R', pt), dtype=np.float32)
            chan_g = np.fromstring(f.channel('G', pt), dtype=np.float32)
            chan_b = np.fromstring(f.channel('B', pt), dtype=np.float32)
            chan_a = np.array([1.0] * len(chan_r), dtype=np.float32)
            dw = f.header()['dataWindow']
            width, height = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
            data = np.empty((len(chan_r) * 4,), dtype=np.float32)
            data[0::4] = chan_r
            data[1::4] = chan_g
            data[2::4] = chan_b
            data[3::4] = chan_a
            data = data.reshape((height, width*4))
            data = np.flipud(data).tobytes()

            # Save cache
            tex_cache = (data, width, height, 'rgba32f', )
            with open(path_cache, 'wb') as fcache:
                cPickle.dump(tex_cache, fcache, -1)

            return Texture2D(data, width, height, 'rgba32f', wrap=wrap, mipmaps=mipmaps)
        else:
            img = Image.open(path)
            if not path.endswith('.bmp'):
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            width, height = img.size
            fmt = img.mode
            data = img.convert('RGBA').tostring("raw", 'RGBA')
            return Texture2D(c_char_p(data), width, height, 'rgba', wrap=wrap, mipmaps=mipmaps)

    def update(self, data):
        """ Update the content of the texture with the given data.

        Note: This is made using a PBO.
        """
        # No PBO exists for this texture. Create one.
        if self.pbo is None:
            self.pbo = BufferObject(GL_PIXEL_UNPACK_BUFFER, self.bytesize, GL_STREAM_DRAW)

        self.bind()
        self._enable_current_unit()

        # Fill the PBO with the user data
        self.pbo.fill(data)

        # Then copy it to the texture
        glTexSubImage2D(self.target, 0, 0, 0, self.width, self.height, self.fmt[0], self.fmt[1], None)
        BufferObject.unbind(GL_PIXEL_UNPACK_BUFFER)

    def _bind_pbo_dl(self):
        if self.pbo_dl is None:
            self.pbo_dl = BufferObject(GL_PIXEL_PACK_BUFFER, self.bytesize, GL_STREAM_READ)
        self.pbo_dl.bind()

    def start_grab(self):
        """ Download back to main memory the texture. 

        Note: This is based on PBO for maximum performance.
        """
        self._bind_pbo_dl()

        self.bind()
        self._enable_current_unit()
        
        # Read the content of the texture back into Main memory
        # This is async and uses DMA to transfer from GPU to Main memory
        glGetTexImage(self.target, 0, self.fmt[0], self.fmt[1], 0)

    def end_grab(self):
        # This blocks
        ptr = self._map()
        buf = string_at(ptr, self.bytesize)
        self._unmap()
        return buf

    def grab_to_file(self, path):
        self.start_grab()
        buf = self.end_grab()
        im = Image.frombuffer(FMT_PIL_MAPPING[self.fmtk], (self.width, self.height), buf)
        im.save(path)

    def _map(self):
        self._bind_pbo_dl()
        return glMapBuffer(GL_PIXEL_PACK_BUFFER, GL_READ_ONLY)

    def _unmap(self):
        self._bind_pbo_dl()
        glUnmapBuffer(GL_PIXEL_PACK_BUFFER)


class Texture3D(GLTexture):
    def __init__(self, data, width, height, depth, format='rgb', filtering='linear'):
        """ Create an OpenGL texture 3D object from user data

        data -- a c_char_p object (can be None if an empty texture object has to be created)
        width -- texture width
        height -- texture height
        depth -- texture depth
        """
        super(Texture3D, self).__init__(GL_TEXTURE_3D, format)

        self.pbo_dl = None
        self.width, self.height, self.depth = width, height, depth
        self.bytesize = self.width * self.height * self.depth * self.fmt[3]
        filtering = GL_LINEAR if filtering == 'linear' else GL_NEAREST

        self._paramf(GL_TEXTURE_WRAP_R, GL_REPEAT)
        self._paramf(GL_TEXTURE_WRAP_S, GL_REPEAT)
        self._paramf(GL_TEXTURE_WRAP_T, GL_REPEAT)        
        self._paramf(GL_TEXTURE_MAG_FILTER, filtering)
        self._paramf(GL_TEXTURE_MIN_FILTER, filtering)

        # Set the data
        glTexImage3D(self.target, 0, self.fmt[2], width, height, depth, 0, self.fmt[0], self.fmt[1], data)

    def _bind_pbo_dl(self):
        if self.pbo_dl is None:
            self.pbo_dl = BufferObject(GL_PIXEL_PACK_BUFFER, self.bytesize, GL_STREAM_READ)
        self.pbo_dl.bind()

    def start_grab(self):
        """ Download back to main memory the texture. 

        Note: This is based on PBO for maximum performance.
        """
        self._bind_pbo_dl()

        self.bind()
        self._enable_current_unit()
        
        # Read the content of the texture back into Main memory
        # This is async and uses DMA to transfer from GPU to Main memory
        glGetTexImage(self.target, 0, self.fmt[0], self.fmt[1], 0)

    def end_grab(self):
        # This blocks
        ptr = self._map()
        buf = string_at(ptr, self.bytesize)
        self._unmap()
        return buf

    def grab_to_file(self, path):
        self.start_grab()
        buf = self.end_grab()
        im = Image.frombuffer(FMT_PIL_MAPPING[self.fmtk], (self.width, self.height * self.depth), buf)
        im.save(path)

    def _map(self):
        self._bind_pbo_dl()
        return glMapBuffer(GL_PIXEL_PACK_BUFFER, GL_READ_ONLY)

    def _unmap(self):
        self._bind_pbo_dl()
        glUnmapBuffer(GL_PIXEL_PACK_BUFFER)