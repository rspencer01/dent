import OpenGL.GL as gl
from Shader import Shader

class GenericShader(Shader):
  def __init__(self, name, frag, vert, geom):
    super(GenericShader,self).__init__(name)
    self.addProgram(gl.GL_VERTEX_SHADER, vert)
    if geom:
      self.addProgram(gl.GL_GEOMETRY_SHADER, geom)
    self.addProgram(gl.GL_FRAGMENT_SHADER, frag)
    self.build()

