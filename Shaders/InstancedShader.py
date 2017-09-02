import OpenGL.GL as gl
from GenericShader import GenericShader
import ctypes

class InstancedShader(GenericShader):
  def __init__(self,name,frag,vert,geom):
    super(InstancedShader,self).__init__(name,frag,vert,geom)

  def setData(self, data, indices, instanced, bufferID=None):
    renderId = super(InstancedShader, self).setData(data, indices)
    self.setInstances(instanced, renderId, bufferID)
    return renderId

  def setInstances(self, instances, renderId, bufferID=None):
    """Sets instance data for the given renderID.  If bufferID is not None, 
    then the instances numpy object is used as a template, and the data is read
    from the buffer specified."""
    gl.glBindVertexArray(self.objInfo[renderId].vertexArray)
    if bufferID == None:
      instbo = gl.glGenBuffers(1)
      gl.glBindBuffer(gl.GL_ARRAY_BUFFER, instbo)
      gl.glBufferData(gl.GL_ARRAY_BUFFER, instances.nbytes, instances, gl.GL_STATIC_DRAW)
    else:
      instbo = bufferID
    self.objInfo[renderId] = self.objInfo[renderId]._replace(instbo=instbo)

    stride = instances.strides[0]
    offsetc = 0
    for i in instances.dtype.names:
      offset = ctypes.c_void_p(offsetc)
      loc = gl.glGetAttribLocation(self.program, i)
      if loc==-1:
        print "Error setting "+i+" in shader "+self.name
        continue
      gl.glBindBuffer(gl.GL_ARRAY_BUFFER, instbo)
      if instances.dtype[i].shape == (4, 4):
        for j in range(4):
          offset = ctypes.c_void_p(offsetc)
          gl.glEnableVertexAttribArray(loc+j)
          gl.glVertexAttribPointer(loc+j, 4, gl.GL_FLOAT, False, stride, offset)
          gl.glVertexAttribDivisor(loc+j, 1)
          offsetc += 16
      elif instances.dtype[i].shape == (4,):
        offset = ctypes.c_void_p(offsetc)
        gl.glEnableVertexAttribArray(loc)
        gl.glVertexAttribPointer(loc, 4, gl.GL_FLOAT, False, stride, offset)
        gl.glVertexAttribDivisor(loc, 1)
        offsetc += 16
      else:
        raise Exception("Type wrong for instanced variable")
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER,0)

  def draw(self, type, objectIndex, num=0, offset=0):
    self.load()
    self._setitems()
    gl.glBindVertexArray(self.objInfo[objectIndex].vertexArray)
    gl.glDrawElementsInstancedBaseInstance(
                               type,
                               self.objInfo[objectIndex].renderVerts,
                               gl.GL_UNSIGNED_INT,
                               None,
                               num,
                               offset
                               )
    gl.glFlush()
