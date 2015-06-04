import logging
import time

from ctypes import *

from PIL import Image

from pogle_opengl import *
from pogle_glprogram import GLProgram
from pogle_fbo import FBO
from pogle_math import Vector, Matrix4x4
from pogle_mesh import GeometryNode
from pogle_scene import SceneNode
from pogle_stats import Stats

__author__ = 'Clement JACOB'
__copyright__ = "Copyright 2013, The Python OpenGL Engine"
__license__ = "Closed Source"
__version__ = "0.0.1"
__email__ = "clems71@gmail.com"
__status__ = "Prototype"


class Material(object):
    _current_shader = None

    def __init__(self, shader, **kwargs):
        self._shader = shader
        self._uniforms = kwargs

    def set(self, name, val):
        self._uniforms[name] = val

    def _use(self):
        """ Make use of the material

        This should not be called by the user. The renderer will call it for
        you.
        """
        if Material._current_shader != self._shader:
            Material._current_shader = self._shader
            self._shader.use()

        for k, v in self._uniforms.iteritems():
            self._shader.set_uniform(k, v)


class RenderPass(object):
    def __init__(self, name, scene, overridematerial=None, fbo=None,
                 clearflags=GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT):
        """
        name -- The name of the pass. Can be used in materials to make use
                of materials per pass
        scene -- The scene to render at that pass
        overridematerial -- If valid, will not use nodes materials, but this
                            material instead
        """
        self.name = name
        self._scene = None
        self.scene = scene
        self.overridematerial = overridematerial
        self.fbo = fbo
        self.clearflags = clearflags
        self.enabled = True
        self.renderlist = None
        self.renderstate = {}

    def mark_renderlist_as_dirty(self):
        self.renderlist = None

    @property
    def scene(self):
        return self._scene

    @scene.setter
    def scene(self, val):
        self.mark_renderlist_as_dirty()

        if not self._scene is None:
            self._scene.unregister_pass(self)

        self._scene = val
        self._scene.register_pass(self)

    def rendered(self, renderer):
        """ Called by the renderer once rendered
        """
        pass

    def _use(self, renderer):
        """ The renderer call it to be prepared to render this pass
        """
        if self.fbo is None:
            FBO.bind_default()
            glViewport(0, 0, renderer.width, renderer.height)
        else:
            self.fbo.bind()
            glViewport(0, 0, self.fbo.width, self.fbo.height)

        renderer.setstate(self.renderstate)

        if self.clearflags != 0:
            glClear(self.clearflags)

    def _capture(self, renderer, path):
        width = renderer.width
        height = renderer.height
        if not self.fbo is None:
            width = self.fbo.width
            height = self.fbo.height

        logging.info('Captured a frame in the render pass \'%s\'' % self.name)

        buf = create_string_buffer(width * height * 4)
        glFlush()
        glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, buf)

        im = Image.frombuffer("RGBA", (width, height), buf)
        im.save(path)


class DefaultForwardRenderingPass(RenderPass):
    def __init__(self, scene):
        super(DefaultForwardRenderingPass, self).__init__(
            'default-forward-pass', scene)


class RenderBucket(object):
    """ A group of nodes that can be rendered efficiently
    """
    SAME_GEOMETRY_FLAG = 0x00000001
    SAME_MATERIAL_FLAG = 0x00000002

    def __init__(self, flags=0x00000000):
        self.flags = flags
        self.nodes = []
        self.geom = None
        self.mat = None

    def add_node(self, node):
        self.nodes.append(node)

    def has_flag(self, flag):
        return ((self.flags & flag) != 0x00000000)

    def __len__(self):
        return len(self.nodes)


class GLRenderer(object):
    DEFAULT_SHADER = """
<shader version="410">
    <vertex><![CDATA[
        DEFINE_VAO_3D_DEFAULT

        void main(void)
        {
            gl_Position = projMatrix * viewMatrix * modelMatrix * position;
        }
    ]]></vertex>
    <fragment><![CDATA[
        out vec4 fragColor;
        
        void main(void)
        {
            fragColor = vec4(1.0, 0.0, 1.0, 0.8);
        }
    ]]></fragment>
</shader>
"""

    def _init_gl(self):
        """ Initialize defaults OpenGL params (used at startup)
        """
        glClearColor(0.0, 0.0, 0.0, 0.0)

        # Tessellation related
        # glPatchParameteri(GL_PATCH_VERTICES, 3)

        # Culling mode
        glCullFace(GL_BACK)

    def _init_materials(self):
        """ Initialize the default materials of the Engine
        """
        default_shader_pink = GLProgram(xml=GLRenderer.DEFAULT_SHADER)
        self.default_mat = Material(default_shader_pink)
        self.current_material = self.default_mat
        self.current_material._use()

    def __init__(self, ctx):
        """ Create a renderer bound to this window.

        width -- Width of the created window
        """
        self.width, self.height = ctx.width(), ctx.height()
        self.ctx = ctx

        self.passes = []

        self.pending_captures = {}

        # Functions to call to apply a state value
        self._state_funcs = {
            'blending': lambda val: self._set_gl_state(GL_BLEND, val),
            'culling': lambda val: self._set_gl_state(GL_CULL_FACE, val),
            'depth_test': lambda val: self._set_gl_state(GL_DEPTH_TEST, val),
            'depthfunc': self._set_depthfunc,
            'blendfunc': self._set_blendfunc,
            'pointsize': self._set_pointsize,
            'blendequ': self._set_blendequ,
        }

        # The default OpenGL state
        self._state_default = {
            'blending': False,
            'culling': True,
            'depth_test': True,
            'depthfunc': GL_LESS,
            'blendfunc': (GL_ONE, GL_ZERO),
            'blendequ': GL_FUNC_ADD,
            'pointsize': 1.0,
        }

        self._current_state = None

    def _set_gl_state(self, flag, val):
        if val:
            glEnable(flag)
        else:
            glDisable(flag)

    def _set_pointsize(self, val):
        glPointSize(val)

    def _set_blendequ(self, val):
        glBlendEquation(val)

    def _set_depthfunc(self, val):
        glDepthFunc(val)

    def _set_blendfunc(self, val):
        glBlendFunc(val[0], val[1])

    @property
    def defaultstate(self):
        return self._state_default

    def setstate(self, renderer_state={}):
        """ Set the renderer state to be the one passed in renderer_state. If
        renderer_state is empty, the state is resetted to the default one.

        WARNING : It also reset the non-passed states to the default ones.
        """

        # Not initialized yet, so fill it with empty state
        if self._current_state is None:
            self._current_state = {}
            for statename in self._state_funcs.iterkeys():
                self._current_state[statename] = None

        # For each state, check if the user gave new one
        for statename, statefunc in self._state_funcs.iteritems():
            new_state = None
            if statename in renderer_state:
                new_state = renderer_state[statename]
            else:
                new_state = self._state_default[statename]

            if new_state != self._current_state[statename]:
                statefunc(new_state)
                self._current_state[statename] = new_state

    def resize(self, w, h):
        self.width = w
        self.height = h

    def init_gl(self):
        # Initialize default OpenGL params
        self._init_gl()

        # Load default materials
        self._init_materials()

        self.setstate()

    def capture(self, pass_, path, callback=None):
        """ Capture the result of the given pass into a file
        """
        self.pending_captures[pass_] = (path, callback)

    def _use_material(self, mat):
        """ Use a new material
        """
        if mat is None:
            mat = self.default_mat

        self.current_material = mat
        self.current_material._use()

    def add_pass(self, pass_):
        self.passes.append(pass_)

        logging.info('Rendering passes are as following')
        for idx, pass_ in enumerate(self.passes):
            logging.info(' >> %d : %s', idx + 1, pass_.name)

    def _generate_render_list(self, pass_):
        lst = set(pass_.scene.get_nodes(SceneNode.NODE_HAS_GEOMETRY))

        pass_.renderlist = []

        # Try to group elements as much as possible
        # Same geometry, same material = instancing if available
        # Same material only = avoid context switches
        # Same geometry only = nothing for the moment
        #   (1 node = 1 render bucket)

        while len(lst) > 0:
            geom_mat_bkt = RenderBucket(RenderBucket.SAME_MATERIAL_FLAG +
                                        RenderBucket.SAME_GEOMETRY_FLAG
                                        )
            mat_bkt = RenderBucket(RenderBucket.SAME_MATERIAL_FLAG)
            default_bkt = RenderBucket()

            # The element to match against
            cur_base_elem = lst.pop()
            cur_base_geom = cur_base_elem.geom
            cur_base_mat = \
                cur_base_elem.material if pass_.overridematerial \
                is None else pass_.overridematerial

            # Add the base element to the bucket
            geom_mat_bkt.add_node(cur_base_elem)
            mat_bkt.add_node(cur_base_elem)
            default_bkt.add_node(cur_base_elem)

            for elem in lst:
                mat = \
                    elem.material if pass_.overridematerial is None \
                    else pass_.overridematerial
                geom = elem.geom

                # Later, we should maybe only check the shader
                if mat == cur_base_mat:
                    if geom == cur_base_geom:
                        geom_mat_bkt.add_node(elem)
                    else:
                        mat_bkt.add_node(elem)

            to_remove_nodes = []
            bkt = None
            if len(geom_mat_bkt) > 1:
                to_remove_nodes = geom_mat_bkt.nodes[1:]
                bkt = geom_mat_bkt
            elif len(mat_bkt) > 1:
                to_remove_nodes = mat_bkt.nodes[1:]
                bkt = mat_bkt
            else:
                bkt = default_bkt

            # Remove nodes added to bucket
            for n in to_remove_nodes:
                lst.remove(n)

            bkt.geom = cur_base_geom
            bkt.mat = cur_base_mat

            # Add the bucket to the render list
            pass_.renderlist.append(bkt)

    def render_pass(self, pass_):
        self.current_pass = pass_
        self.current_camera = pass_.scene.camera
        if self.current_camera._follow_viewport is True:
            c = self.current_camera
            self.current_camera.proj = Matrix4x4.perspective(
                c._fovy,
                float(self.width) / float(self.height),
                c._near,
                c._far)

        pass_._use(self)

        # Generate the render list the most efficient possible, avoiding
        # too much context switches.
        if pass_.renderlist is None:
            self._generate_render_list(pass_)

        # Effectively render the buckets
        for bkt in pass_.renderlist:
            self._use_material(bkt.mat)

            # Bucket uniforms
            self.current_material._shader.set_uniform(
                'viewMatrix',
                self.current_camera.view)
            self.current_material._shader.set_uniform(
                'projMatrix',
                self.current_camera.proj)

            if len(pass_.scene.lights) != 0:
                self.current_material._shader.set_uniform(
                    'lightPos',
                    pass_.scene.lights[0].position)

            for node in bkt.nodes:
                # Per instance uniform
                self.current_material._shader.set_uniform(
                    'modelMatrix',
                    node.transform.premul_matrix)
                node.render(self)

        # Signal the event to the pass, that it has been rendered properly
        pass_.rendered(self)

    def render(self):
        """ Effectively render all the enabled passes
        """

        Stats.clear()

        for pass_ in self.passes:
            if not pass_.enabled:
                continue

            self.render_pass(pass_)

            # If any capture is pending for this pass, then, capture!
            # and remove from pending list
            callback = None
            if pass_ in self.pending_captures:
                pass_._capture(self, self.pending_captures[pass_][0])
                callback = self.pending_captures[pass_][1]
                del self.pending_captures[pass_]
            if pass_.name in self.pending_captures:
                pass_._capture(self, self.pending_captures[pass_.name][0])
                callback = self.pending_captures[pass_.name][1]
                del self.pending_captures[pass_.name]

            if callback:
                callback()
