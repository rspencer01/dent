import OpenGL.GL as gl
import ctypes
from .Shader import Shader
import logging


class TransformFeedbackShader(Shader):

    def __init__(self, name, vertex, geometry=None):
        super(TransformFeedbackShader, self).__init__(name)
        self._sources[gl.GL_VERTEX_SHADER] = vertex
        if geometry:
            self._sources[gl.GL_GEOMETRY_SHADER] = geometry
        self.program = gl.glCreateProgram()

    def addOutput(self, name):
        """Registers an output of the transform shader."""
        varyings = ctypes.c_char_p(name)
        varyings_pp = ctypes.cast(
            ctypes.pointer(varyings), ctypes.POINTER(ctypes.POINTER(gl.GLchar))
        )
        gl.glTransformFeedbackVaryings(
            self.program, 1, varyings_pp, gl.GL_INTERLEAVED_ATTRIBS
        )

    def getOutputBufferObject(self, objectIndex, max_size):
        """Gets an output buffer for the given input object.

        TODO Not sure about this here.  How should we be doing this better?"""
        tbo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.objInfo[objectIndex].vertexArray)
        gl.glBindBuffer(gl.GL_TRANSFORM_FEEDBACK_BUFFER, tbo)
        gl.glBufferData(
            gl.GL_TRANSFORM_FEEDBACK_BUFFER, max_size, None, gl.GL_STATIC_DRAW
        )
        gl.glBindBufferBase(gl.GL_TRANSFORM_FEEDBACK_BUFFER, 0, tbo)

        return tbo

    def read_output_buffer(self, tbo, count):
        gl.glBindBufferBase(gl.GL_TRANSFORM_FEEDBACK_BUFFER, 0, tbo)
        return gl.glGetBufferSubData(gl.GL_TRANSFORM_FEEDBACK_BUFFER, 0, count)

    def draw(self, type, objectIndex, tbo, count=0):
        """Starts a transform feedback draw.  Return the number of items actually
        created (may differ from `num` due to geometry shaders)."""
        self.load()
        self._setitems()
        gl.glBindVertexArray(self.objInfo[objectIndex].vertexArray)
        gl.glBindBufferBase(gl.GL_TRANSFORM_FEEDBACK_BUFFER, 0, tbo)
        gl.glEnable(gl.GL_RASTERIZER_DISCARD)
        query = gl.glGenQueries(1)
        gl.glBeginQuery(gl.GL_TRANSFORM_FEEDBACK_PRIMITIVES_WRITTEN, query)
        gl.glBeginTransformFeedback(type)
        gl.glDrawArrays(gl.GL_POINTS, 0, count)
        gl.glEndTransformFeedback()
        gl.glEndQuery(gl.GL_TRANSFORM_FEEDBACK_PRIMITIVES_WRITTEN)
        gl.glDisable(gl.GL_RASTERIZER_DISCARD)
        gl.glFlush()
        count = gl.glGetQueryObjectiv(query, gl.GL_QUERY_RESULT)
        gl.glDeleteQueries(1, [query])
        return count

    def build(self):
        """Builds the shader.

        We need a custom shader build function because the trasform feedback shaders
        require varyings to be set before the program is linked."""
        logging.debug("Building shader {}".format(self.name))
        for source in list(self._sources.values()):
            gl.glAttachShader(self.program, source.get_program())

        gl.glLinkProgram(self.program)
        if gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS) != gl.GL_TRUE:
            raise RuntimeError(gl.glGetProgramInfoLog(self.program))
