#!/usr/bin/env python

import os

from pogle import *

CWD = os.path.abspath(os.path.dirname(__file__))

class App(GLFWRenderer):
    def __init__(self):
        super(App, self).__init__(size=(512, 512))

    def setup(self):
        self.shader_sdf = GLProgram(os.path.join(CWD, 'sdf.xml'))
        self.shader_shade = GLProgram(os.path.join(CWD, 'shade.xml'))

        depth_tex = Texture2D(None, 512, 512, format='rgba32f', filtering='linear')
        self.fbo = FBO(color0=depth_tex)

        self.scene = Scene()
        self.quad = GeometryNode(FullScreenQuad())
        self.scene.add_node(self.quad)

        self.renderer.add_pass(RenderPass(
            'depth-render-sdf', 
            self.scene, 
            overridematerial=Material(self.shader_sdf),
            fbo=self.fbo
            ))

        self.renderer.add_pass(RenderPass(
            'render-shaded',
            self.scene,
            overridematerial=Material(self.shader_shade, depth=depth_tex),
            ))

        # self.renderer.add_pass(DefaultForwardRenderingPass(self.scene))

if __name__ == '__main__':
    app = App()
    app.run()
