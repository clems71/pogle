import logging

# POGLE imports
from pogle_renderer import GLRenderer

import cyglfw3 as glfw

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"


class GLFWRenderer(object):
    def __init__(self, format=(3, 2), size=(800, 600), title='GLFW Renderer', hidden=False):
        # Make a window
        glfw.Init()
        glfw.WindowHint(glfw.CONTEXT_VERSION_MAJOR, format[0])
        glfw.WindowHint(glfw.CONTEXT_VERSION_MINOR, format[1])
        glfw.WindowHint(glfw.OPENGL_FORWARD_COMPAT, 1)
        glfw.WindowHint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        if hidden:
            glfw.WindowHint(glfw.VISIBLE, 0)
            glfw.WindowHint(glfw.FOCUSED, 0)
        self.window = glfw.CreateWindow(size[0], size[1], title)
        glfw.MakeContextCurrent(self.window)

        # Retina display support
        self.size = glfw.GetFramebufferSize(self.window)

        logging.basicConfig(level=logging.DEBUG)
        self.renderer = GLRenderer(self)

        self.renderer.init_gl()
        self.renderer.resize(*self.size)
        self.setup()

    def width(self):
        return self.size[0]

    def height(self):
        return self.size[1]

    def run(self):
        while not glfw.WindowShouldClose(self.window):
            self.update()
            self.renderer.render()
            glfw.SwapBuffers(self.window)
            glfw.PollEvents()

    def setup(self):
        pass

    def update(self):
        pass

    # Exposed interface
    def key_pressed(self, key, char, modifiers):
        pass
    def mouse_click(self, x, y, buttons):
        pass
    def mouse_drag(self, x, y, dx, dy, buttons):
        pass
    def mouse_release(self):
        pass        

def main():
    rdr = GLFWRenderer()
    rdr.run()

if __name__ == '__main__':
    main()
