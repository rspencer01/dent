import OpenGL.GL as gl
import Object
import logging
import numpy as np
import Shaders
import Texture

rendered = set()

shader              = Shaders.getShader('general', instance=True)
shader['colormap']  = Texture.COLORMAP_NUM
shader['normalmap'] = Texture.NORMALMAP_NUM
shader['bumpmap']   = Texture.BUMPMAP_NUM

class InstancedObject(Object.Object):
  def __init__(self, *args, **kwargs):
    super(InstancedObject, self).__init__(*args, daemon=False, **kwargs)
    self.instances = np.zeros(0, dtype=[("model", np.float32, (4, 4))])

  def uploadMesh(self, data, indices, mesh):
    """Intercepted so that we can do the whole instancing thing."""
    pass

  def display(self, offset=0, num=None):
    if num is None:
      num = len(self)
    shader.load()
    options = None

    for meshdatum, renderid in zip(self.meshes, self.renderIDs):
      # Set options
      if options != Object.getOptionNumber(meshdatum.options):
        options = Object.getOptionNumber(meshdatum.options)
        shader['options'] = options
      meshdatum.colormap.load()
      if meshdatum.options.has_bumpmap:
        meshdatum.normalmap.load()
      shader.draw(gl.GL_TRIANGLES, renderid, num, offset)

  def __len__(self):
    return len(self.instances)

  def addInstances(self,data):
    self.instances = np.append(self.instances, data)
    logging.info("Adding {} instances".format(len(data)))

  def freeze(self):
    logging.info("Freezing {}".format(self))
    for mesh in self.meshes:
      self.renderIDs.append(shader.setData(mesh.data, mesh.indices, self.instances))

  def refreeze(self):
    for renderid in self.renderIDs:
      gl.glBindBuffer(gl.GL_ARRAY_BUFFER, shader.objInfo[renderid].instbo)
      gl.glBufferData(gl.GL_ARRAY_BUFFER, self.instances.nbytes, self.instances, gl.GL_STREAM_DRAW)
