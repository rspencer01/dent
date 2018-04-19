import OpenGL.GL as gl
import core
from Shader import Shader


class GenericShader(Shader):

    def __init__(self, name, frag, vert, geom):
        super(GenericShader, self).__init__(name)
        self._sources = {}

        self._sources[gl.GL_VERTEX_SHADER] = vert
        if geom:
            self._sources[gl.GL_GEOMETRY_SHADER] = geom
        self._sources[gl.GL_FRAGMENT_SHADER] = frag

        for program in self._sources:
            self.addProgram(program, self._sources[program])

        self.build()

    def reload(self):
        for i in self._sources:
            self._sources[i].load_from_source()
        gl.glDeleteProgram(self.program)
        self.program = gl.glCreateProgram()
        for program in self._sources:
            self.addProgram(program, self._sources[program])

        self.build()
        core.setUniversalUniforms(self)
