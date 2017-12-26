from dent.RectangleObjects import RectangleObject
from dent.RenderStage import RenderStage
from dent.RenderPipeline import RenderPipeline
import dent.Texture
import numpy as np

class PhongLightingStage():
  def __init__(self, final_stage=False):
    self.renderPipeline = RenderPipeline([
        RenderStage(render_func=self.ssao_pass),
        RenderStage(render_func=self.hblur_pass),
        RenderStage(render_func=self.vblur_pass),
        RenderStage(render_func=self.lighting_pass, clear_depth=False, final_stage=final_stage)
      ])

    self._lighting_rectangle_object = RectangleObject('lighting')
    self._lighting_rectangle_object.shader['colormap'] = dent.Texture.COLORMAP_NUM
    self._lighting_rectangle_object.shader['normalmap'] = dent.Texture.COLORMAP2_NUM
    self._lighting_rectangle_object.shader['positionmap'] = dent.Texture.COLORMAP3_NUM
    self._lighting_rectangle_object.shader['ssaomap'] = dent.Texture.SSAOMAP_NUM

    self._ssao_rectangle_object = RectangleObject('ssao')
    self._ssao_rectangle_object.shader['colormap'] = dent.Texture.COLORMAP_NUM
    self._ssao_rectangle_object.shader['normalmap'] = dent.Texture.COLORMAP2_NUM
    self._ssao_rectangle_object.shader['positionmap'] = dent.Texture.COLORMAP3_NUM

    self._hblur_rectangle_object = RectangleObject('gaussian')
    self._hblur_rectangle_object.shader['colormap'] = dent.Texture.COLORMAP_NUM

    self._vblur_rectangle_object = RectangleObject('gaussian')
    self._vblur_rectangle_object.shader['colormap'] = dent.Texture.COLORMAP_NUM

    self.sunIntensity = 1.
    self.backgroundColor = np.zeros(4, dtype=float)
    self.enabled = True


  def ssao_pass(self, width, height, previous_stage, **kwargs):
    self._actual_previous_stage.displayColorTexture.load()
    self._actual_previous_stage.displaySecondaryColorTexture.load()
    self._actual_previous_stage.displayAuxColorTexture.load()

    self._ssao_rectangle_object.display()


  def hblur_pass(self, width, height, previous_stage, **kwargs):
    previous_stage.displayColorTexture.load()

    self._hblur_rectangle_object.shader['direction'] = np.array([1.,0])
    self._hblur_rectangle_object.display()


  def vblur_pass(self, width, height, previous_stage, **kwargs):
    previous_stage.displayColorTexture.load()

    self._vblur_rectangle_object.shader['direction'] = np.array([0,1.])
    self._vblur_rectangle_object.display()


  def lighting_pass(self, width, height, previous_stage, **kwargs):
    self._actual_previous_stage.displayColorTexture.load()
    self._actual_previous_stage.displaySecondaryColorTexture.load()
    self._actual_previous_stage.displayAuxColorTexture.load()
    self.vblur_stage.displayColorTexture.loadAs(dent.Texture.SSAOMAP)

    self._lighting_rectangle_object.shader['sunIntensity'] = self.sunIntensity
    self._lighting_rectangle_object.shader['backgroundColor'] = self.backgroundColor
    self._lighting_rectangle_object.display()


  def load(self, width, height, offsetx=0, offsety=0, clear=None):
    pass


  def reshape(self, width, height=None):
    for stage in self.renderPipeline.stages:
      stage.reshape(width, height)


  def render(self, width, height, previous_stage):
    self._actual_previous_stage = previous_stage
    self.renderPipeline.run(width, height)
