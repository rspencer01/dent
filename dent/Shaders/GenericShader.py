import OpenGL.GL as gl
from . import core
from .Shader import Shader


class GenericShader(Shader):

    def __init__(self, name, frag, vert, geom):
        super(GenericShader, self).__init__(name)

        self._sources[gl.GL_VERTEX_SHADER] = vert
        if geom:
            self._sources[gl.GL_GEOMETRY_SHADER] = geom
        self._sources[gl.GL_FRAGMENT_SHADER] = frag

        self.build()
