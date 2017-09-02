import OpenGL.GL as gl
import ctypes
from Shader import Shader

class TransformFeedbackShader(Shader):
  def addOutput(self, name):
    """Registers an output of the transform shader."""
    varyings = ctypes.c_char_p(name)
    varyings_pp = ctypes.cast(ctypes.pointer(varyings), ctypes.POINTER(ctypes.POINTER(gl.GLchar)))
    gl.glTransformFeedbackVaryings(self.program, 1, varyings_pp, gl.GL_INTERLEAVED_ATTRIBS)

  def getOutputBufferObject(self, objectIndex, max_size):
    """Gets an output buffer for the given input object.

    TODO Not sure about this here.  How should we be doing this better?"""
    tbo = gl.glGenBuffers(1)

    gl.glBindVertexArray(self.objInfo[objectIndex].vertexArray)
    gl.glBindBuffer(gl.GL_TRANSFORM_FEEDBACK_BUFFER, tbo)
    gl.glBufferData(gl.GL_TRANSFORM_FEEDBACK_BUFFER, max_size, None, gl.GL_STATIC_DRAW)
    gl.glBindBufferBase(gl.GL_TRANSFORM_FEEDBACK_BUFFER, 0, tbo)

    return tbo

  def draw(self, type, objectIndex, count=0):
    """Starts a transform feedback draw.  Return the number of items actually
    created (may differ from `num` due to geometry shaders)."""
    self.load()
    self._setitems()
    gl.glBindVertexArray(self.objInfo[objectIndex].vertexArray)
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
