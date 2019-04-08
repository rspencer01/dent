import OpenGL.GL as gl
from . import Object
import logging
import numpy as np
from . import Shaders
from . import Texture

rendered = set()


class InstancedObject(Object.Object):
  def __init__(self, *args, **kwargs):
    self.md = {}
    super(InstancedObject, self).__init__(*args, daemon=False, **kwargs)
    self.instances = np.zeros(0, dtype=[("model", np.float32, (4, 4))])
    self.shader = Shaders.getShader('general', instance=True)
    self.shader['colormap']  = Texture.COLORMAP_NUM
    self.shader['normalmap'] = Texture.NORMALMAP_NUM
    self.shader['bumpmap'] = Texture.BUMPMAP_NUM

  def uploadMesh(self, mesh):
    """Intercepted so that we can do the whole instancing thing."""
    self.md[mesh.name] = (mesh.data, mesh.indices)

  def display(self, offset=0, num=None):
    if num is None:
      num = len(self)
    self.shader.load()
    options = None

    for material in list(self.materials.values()):
        material.set_uniforms(self.shader)
        for mesh in self.meshes_per_material[material.name]:
            if mesh.name in self.renderIDs:
                self.shader.draw(gl.GL_TRIANGLES, self.renderIDs[mesh.name], num, offset)

  def __len__(self):
    return len(self.instances)

  def addInstances(self,data):
    self.instances = np.append(self.instances, data)
    logging.info("Adding {} instances".format(len(data)))

  def freeze(self):
    logging.info("Freezing {}".format(self))
    for mesh in self.meshes:
      self.renderIDs[mesh.name] = self.shader.setData(*self.md[mesh.name], self.instances)

  def refreeze(self):
    for renderid in self.renderIDs.values():
      gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.shader.objInfo[renderid].instbo)
      gl.glBufferData(gl.GL_ARRAY_BUFFER, self.instances.nbytes, self.instances, gl.GL_STREAM_DRAW)
