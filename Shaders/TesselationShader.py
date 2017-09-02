import OpenGL.GL as gl
from Shader import Shader

class TesselationShader(Shader):
  def __init__(self, name, frag, vert, geom, tessC, tessE):
    super(TesselationShader, self).__init__(name)
    self.addProgram(gl.GL_VERTEX_SHADER, vert)
    if geom:
      self.addProgram(gl.GL_GEOMETRY_SHADER, geom)
    self.addProgram(gl.GL_FRAGMENT_SHADER, frag)
    self.addProgram(gl.GL_TESS_CONTROL_SHADER, tessC)
    self.addProgram(gl.GL_TESS_EVALUATION_SHADER, tessE)
    self.build()

  def draw(self, number, objectIndex):
    self.load()
    self._setitems()
    gl.glBindVertexArray(self.objInfo[objectIndex].vertexArray)
    gl.glPatchParameteri(gl.GL_PATCH_VERTICES, 3)
    gl.glDrawArrays(gl.GL_PATCHES, 0, number)
    gl.glFlush()
