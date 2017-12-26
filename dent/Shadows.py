import OpenGL.GL as gl
import Texture
from RenderStage import RenderStage
import transforms
import Shaders
import Camera
import numpy as np

SHADOW_SIZE = 2048

class Shadows(object):

  def __init__(self, render_func, lock_object, rng=15):

    self.shadowCamera = Camera.Camera(np.array([0.,300,0]), lockObject=None, lockDistance=2000)
    self.shadowCamera.lockObject = lock_object
    self.shadowCamera.update()

    self.render_func = render_func
    self.renderStages = [RenderStage(depth_only=True) for _ in xrange(3)]
    for i in self.renderStages:
      i.reshape(SHADOW_SIZE, SHADOW_SIZE)
    self.renderStages[0].displayDepthTexture.loadAs(Texture.SHADOWS1)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_COMPARE_MODE, gl.GL_COMPARE_REF_TO_TEXTURE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_COMPARE_FUNC, gl.GL_GREATER)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    self.renderStages[1].displayDepthTexture.loadAs(Texture.SHADOWS2)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_COMPARE_MODE, gl.GL_COMPARE_REF_TO_TEXTURE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_COMPARE_FUNC, gl.GL_GREATER)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    self.renderStages[2].displayDepthTexture.loadAs(Texture.SHADOWS3)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_COMPARE_MODE, gl.GL_COMPARE_REF_TO_TEXTURE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_COMPARE_FUNC, gl.GL_GREATER)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)

    self.projections = []
    for i in range(3):
      width = 20 * rng**i
      self.projections.append(transforms.ortho(-width,width,-width,width, 2000. - 2*width, 2000. + 2*width))
      Shaders.updateUniversalUniform('shadowProjection'+str(i+1),self.projections[i])

    Shaders.updateUniversalUniform('shadowTexture1',Texture.SHADOWS1_NUM)
    Shaders.updateUniversalUniform('shadowTexture2',Texture.SHADOWS2_NUM)
    Shaders.updateUniversalUniform('shadowTexture3',Texture.SHADOWS3_NUM)

    self.count = 0
    self.exponent = 2


  def clear(self):
    for i in xrange(3):
      self.renderStages[i].load(SHADOW_SIZE, SHADOW_SIZE)


  def render(self):
    self.shadowCamera.update()
    self.shadowCamera.render()
    self.count += 1
    for i in xrange(3):
      if self.count % (self.exponent ** i) != 0:
        continue
      self.renderStages[i].load(SHADOW_SIZE, SHADOW_SIZE)
      Shaders.setUniform('projection',self.projections[i])
      self.shadowCamera.render('shadow'+str(i+1))

      self.render_func()
