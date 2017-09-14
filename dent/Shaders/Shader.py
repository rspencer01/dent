import OpenGL.GL as gl
from collections import namedtuple
import ctypes
import numpy as np
import logging

currentShader = None

objectInfo = namedtuple("ObjectInfo",
    ("numVertices",
      "numIndices",
      "vbo",
      "vertexArray",
      "ibo",
      "renderVerts",
      "instbo",
      "transformBufferObject"))

class Shader(object):
  def __init__(self, name):
    # Who are we
    self.name = name
    # What do we stand for?
    self.program = gl.glCreateProgram()
    self.programs = []
    # Where the uniform variables live
    self.locations = {}
    # The info for the objects of this shader
    self.objInfo = []
    # The errorful variables we have seen before
    self.warned = set()
    # Uniforms that are still to be set
    self.unsetUniforms = {}

  def addProgram(self, type, source):
    """Creates a shader, compiles the given shader source and attaches it
    to this program."""
    gl.glAttachShader(self.program, source.getProgram())

  def build(self):
    # Link!  Everything else is done in addProgram
    gl.glLinkProgram(self.program)
    if gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS) != gl.GL_TRUE:
      raise RuntimeError(gl.glGetProgramInfoLog(self.program))
    for prog in self.programs:
      gl.glDetachShader(self.program, prog)

  def load(self):
    # Check if we are loaded already.  If not do so.
    global currentShader
    if currentShader != self:
      gl.glUseProgram(self.program)
      currentShader = self

  def setData(self,data, indices=[], instanced=False):
    """Given vertex data and triangle indices, gives a unique identifier to be
    used when rendering this object."""
    vbo = gl.glGenBuffers(1)
    ibo = gl.glGenBuffers(1)
    vertexArray = gl.glGenVertexArrays(1)
    gl.glBindVertexArray(vertexArray)
    self.objInfo.append( objectInfo(len(data),
                                    len(indices),
                                    vbo,
                                    vertexArray,
                                    ibo,
                                    len(indices)*3,
                                    None, None
                                    ) )

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, data.nbytes, data, gl.GL_STATIC_DRAW)
    stride = data.strides[0]
    offsetc = 0
    for i in data.dtype.names:
      offset = ctypes.c_void_p(offsetc)
      loc = gl.glGetAttribLocation(self.program, i)
      if loc==-1:
        # Not in shader
        offsetc += data.dtype[i].itemsize
        continue
      gl.glEnableVertexAttribArray(loc)
      gl.glBindBuffer(gl.GL_ARRAY_BUFFER,vbo)
      gl.glVertexAttribPointer(loc, int(np.prod(data.dtype[i].shape)), gl.GL_FLOAT, False, stride, offset)
      gl.glVertexAttribDivisor(loc, 0)
      offsetc += data.dtype[i].itemsize

    if indices != []:
      gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ibo)
      gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW);

    return len(self.objInfo)-1

  def deleteData(self,dataId):
    obj = self.objInfo[dataId]
    gl.glDeleteBuffers(3, [obj.vbo,obj.ibo])
    gl.glDeleteVertexArrays(1, [obj.vertexArray])

  def __setitem__(self,i,v):
    """Sets the uniform lazily.  That is, we store the uniform CPU side, and 
    only blit it once we are about to render.  See `_setitem`."""
    self.unsetUniforms[i] = v

  def _setitem(self,i,v):
    """Sets the uniform in the shader.  Due to GPU overhead, this is not called 
    via the [] notation, but only when we render."""
    if i not in self.locations:
      self.locations[i] = gl.glGetUniformLocation(self.program, i)
    loc = self.locations[i]
    if loc==-1:
      if not i in self.warned:
        logging.warn("No uniform {} in shader {}".format(i, self.name))
        self.warned.add(i)
    elif type(v) == np.ndarray and len(v.shape) == 3 and v.shape[1:] == (4, 4):
      gl.glUniformMatrix4fv(loc, v.shape[0], gl.GL_FALSE, v)
    elif type(v) == np.ndarray and v.shape == (4, 4):
      gl.glUniformMatrix4fv(loc, 1, gl.GL_FALSE, v)
    elif type(v) == np.ndarray and v.shape == (3, 3):
      gl.glUniformMatrix3fv(loc, 1, gl.GL_FALSE, v)
    elif type(v) == np.ndarray and len(v.shape)==2 and v.shape[1]==3:
      gl.glUniform3fv(loc, v.shape[0], v)
    elif type(v) == np.ndarray and len(v.shape)==2 and v.shape[1]==4:
      gl.glUniform4fv(loc, v.shape[0], v)
    elif type(v) in [float, np.float32, np.float64]:
      gl.glUniform1f(loc,v)
    elif type(v) in [np.ndarray] and v.shape==(3,):
      gl.glUniform3f(loc, v[0], v[1], v[2])
    elif type(v) in [np.ndarray] and v.shape==(2,):
      gl.glUniform2f(loc, v[0], v[1])
    elif type(v) in [int]:
      gl.glUniform1i(loc, v)

  def _setitems(self):
    """Blits all the lazyloaded uniforms to the GPU.    """
    for i,v in self.unsetUniforms.items():
      self._setitem(i,v)
    self.unsetUniforms = {}

  def draw(self,type,objectIndex,num=0):
    self.load()
    self._setitems()
    gl.glBindVertexArray(self.objInfo[objectIndex].vertexArray)
    gl.glDrawElements(type,self.objInfo[objectIndex].numIndices,gl.GL_UNSIGNED_INT,None)
    gl.glFlush()
