from dent.RectangleObjects import RectangleObject
from dent.RenderStage import RenderStage
import dent.Texture
import numpy as np

class PhongLightingStage():
  def __init__(self, final_stage=False):
    self.ssao_stage = RenderStage(render_func=self.ssao_pass)
    self.hblur_stage = RenderStage(render_func=self.hblur_pass)
    self.vblur_stage = RenderStage(render_func=self.vblur_pass)
    self.last_stage = RenderStage(render_func=self.lighting_pass, clear_depth=False, final_stage=final_stage)

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
    self.ssao_stage.load(width, height, 0, 0, True)
    previous_stage.displayColorTexture.load()
    previous_stage.displaySecondaryColorTexture.load()
    previous_stage.displayAuxColorTexture.load()
    self._ssao_rectangle_object.display()


  def hblur_pass(self, width, height, previous_stage, **kwargs):
    self.hblur_stage.load(width, height, 0, 0, True)
    self.ssao_stage.displayColorTexture.load()
    self._hblur_rectangle_object.shader['direction'] = np.array([1.,0])
    self._hblur_rectangle_object.display()


  def vblur_pass(self, width, height, previous_stage, **kwargs):
    self.vblur_stage.load(width, height, 0, 0, True)
    self.hblur_stage.displayColorTexture.load()
    self._vblur_rectangle_object.shader['direction'] = np.array([0,1.])
    self._vblur_rectangle_object.display()


  def lighting_pass(self, width, height, previous_stage, **kwargs):
    self.last_stage.load(width, height, 0, 0, True)
    previous_stage.displayColorTexture.load()
    previous_stage.displaySecondaryColorTexture.load()
    previous_stage.displayAuxColorTexture.load()
    self.vblur_stage.displayColorTexture.loadAs(dent.Texture.SSAOMAP)
    self._lighting_rectangle_object.shader['sunIntensity'] = self.sunIntensity
    self._lighting_rectangle_object.shader['backgroundColor'] = self.backgroundColor
    self._lighting_rectangle_object.display()


  def load(self, width, height, offsetx=0, offsety=0, clear=None):
    pass


  def reshape(self, width, height=None):
    self.ssao_stage.reshape(width, height)
    self.hblur_stage.reshape(width, height)
    self.vblur_stage.reshape(width, height)
    self.last_stage.reshape(width, height)


  def render(self, width, height, previous_stage):
    self.ssao_stage.load(width, height, clear=True)
    self.ssao_stage.render(width, height, previous_stage)
    self.hblur_stage.load(width, height, clear=True)
    self.hblur_stage.render(width, height, previous_stage)
    self.vblur_stage.load(width, height, clear=True)
    self.vblur_stage.render(width, height, previous_stage)
    self.last_stage.load(width, height)
    self.last_stage.render(width, height, previous_stage)
