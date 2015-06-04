#!/usr/bin/env python

from pogle import *

class App(GLFWRenderer):
    def __init__(self):
        super(App, self).__init__()

    def setup(self):
        self.scene = Scene()
        self.quad = GeometryNode(FullScreenQuad())
        self.scene.add_node(self.quad)
        self.renderer.add_pass(DefaultForwardRenderingPass(self.scene))

if __name__ == '__main__':
    app = App()
    app.run()
