import Texture
from RenderStage import RenderStage
import transforms
import Shaders
import Camera
import numpy as np

SHADOW_SIZE = 1024

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
    self.renderStages[1].displayDepthTexture.loadAs(Texture.SHADOWS2)
    self.renderStages[2].displayDepthTexture.loadAs(Texture.SHADOWS3)

    self.projections = []
    for i in range(3):
      width = 20 * rng**i
      self.projections.append(transforms.ortho(-width,width,-width,width, 2000. - 2*width, 2000. + 2*width))
      Shaders.updateUniversalUniform('shadowProjection'+str(i+1),self.projections[i])

    Shaders.updateUniversalUniform('shadowTexture1',Texture.SHADOWS1_NUM)
    Shaders.updateUniversalUniform('shadowTexture2',Texture.SHADOWS2_NUM)
    Shaders.updateUniversalUniform('shadowTexture3',Texture.SHADOWS3_NUM)


  def render(self):
    self.shadowCamera.update()
    self.shadowCamera.render()
    for i in xrange(3):
      self.renderStages[i].load(SHADOW_SIZE, SHADOW_SIZE)
      Shaders.setUniform('projection',self.projections[i])
      self.shadowCamera.render('shadow'+str(i+1))

      self.render_func()
