from dent.Camera import Camera
from dent.RenderPipeline import RenderPipeline
from dent.RenderStage import RenderStage
import dent.Texture
from dent.RectangleObjects import RectangleObject
import numpy as np

class Scene(object):
  def __init__(self):
    self.camera = Camera()
    self.renderPipeline = RenderPipeline(
        [RenderStage(render_func=self.display, final_stage=True)]
        )

  def render(self, windowWidth, windowHeight):
    self.renderPipeline.run(windowWidth, windowHeight)

  def display(self, **kwargs):
    pass


class DeferredRenderScene(Scene):
  def __init__(self):
    self.camera = Camera()
    self.renderPipeline = RenderPipeline(
        [
          RenderStage(render_func=self.display, aux_buffer=True),
          RenderStage(render_func=self._lighting_display, clear_depth=False, final_stage=True)
        ]
      )

    self._lighting_rectangle_object = RectangleObject('lighting')
    self._lighting_rectangle_object.shader['colormap'] = dent.Texture.COLORMAP_NUM
    self._lighting_rectangle_object.shader['normalmap'] = dent.Texture.COLORMAP2_NUM
    self._lighting_rectangle_object.shader['positionmap'] = dent.Texture.COLORMAP3_NUM
    self.sunIntensity = 1.
    self.backgroundColor = np.zeros(4, dtype=float)

  def _lighting_display(self, previous_stage, **kwargs):
    previous_stage.displayColorTexture.load()
    previous_stage.displaySecondaryColorTexture.load()
    previous_stage.displayAuxColorTexture.load()
    self._lighting_rectangle_object.shader['sunIntensity'] = self.sunIntensity
    self._lighting_rectangle_object.shader['backgroundColor'] = self.backgroundColor
    self._lighting_rectangle_object.display()
