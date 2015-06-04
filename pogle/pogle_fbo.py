from pogle_opengl import *
from pogle_gltexture import Texture2D, Texture3D

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"

class Texture3DAttachment(object):
    def __init__(self, tex3d, z=0):
        self._texture3d = tex3d
        self._z = z

class FBO(object):
    ATTACHMENT_MAPPING = {
        'depth'  : GL_DEPTH_ATTACHMENT,
        'color0' : GL_COLOR_ATTACHMENT0,
        'color1' : GL_COLOR_ATTACHMENT1,
        'color2' : GL_COLOR_ATTACHMENT2,
    }

    _current = None

    def __init__(self, **kwargs):
        self.fboid = glGenFramebuffers(1)
        self.bind()

        self.width = 0
        self.height = 0

        self.set_attachments(**kwargs)

        # Initialize it properly, in a known state
        self.clear()

    def set_attachments(self, **kwargs):
        self.bind()

        color_buf = False
        depth_buf = False

        self.attachments = kwargs

        for k, v in kwargs.iteritems():
            attach_type = type(v)

            if attach_type == Texture2D:
                gl_attachment = FBO.ATTACHMENT_MAPPING[k]
                glFramebufferTexture2D(GL_FRAMEBUFFER, gl_attachment, v.target, v.texid, 0)

                if v.width > self.width:
                    self.width = v.width
                if v.height > self.height:
                    self.height = v.height

                if k.startswith('color'):
                    color_buf = True
                elif k.startswith('depth'):
                    depth_buf = True

            elif attach_type == Texture3DAttachment:
                gl_attachment = FBO.ATTACHMENT_MAPPING[k]
                glFramebufferTexture3D(GL_FRAMEBUFFER, gl_attachment, v._texture3d.target, v._texture3d.texid, 0, v._z)

                if v._texture3d.width > self.width:
                    self.width = v._texture3d.width
                if v._texture3d.height > self.height:
                    self.height = v._texture3d.height

                if k.startswith('color'):
                    color_buf = True
                elif k.startswith('depth'):
                    depth_buf = True

        if len(kwargs) != 0:
            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            if status != GL_FRAMEBUFFER_COMPLETE:
                raise Exception('Could not create the FBO')

        # No color buffer ? so disable draw buffer
        # if color_buf == False:
        #     glReadBuffer(GL_NONE)
        #     glDrawBuffer(GL_NONE)

        self.clearflags = 0
        self.clearflags |= GL_COLOR_BUFFER_BIT if color_buf else 0
        self.clearflags |= GL_DEPTH_BUFFER_BIT if depth_buf else 0        

    def clear(self):
        if self.clearflags != 0:
            self.bind()
            glClear(self.clearflags)

    def __del__(self):
        glDeleteFramebuffers([self.fboid])
        glFlush()

    def bind(self):
        if FBO._current != self:
            glBindFramebuffer(GL_FRAMEBUFFER, self.fboid)
            FBO._current = self

    @staticmethod
    def bind_default():
        if FBO._current != None:
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            FBO._current = None

    def start_grab(self):
        self.bind()
        col0_tex = self.attachments['color0']
        col0_tex._bind_pbo_dl()
        glReadPixels(0, 0, col0_tex.width, col0_tex.height, col0_tex.fmt[0], col0_tex.fmt[1], 0)

    def end_grab(self):
        return self.attachments['color0'].end_grab()
