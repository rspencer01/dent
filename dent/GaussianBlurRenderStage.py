import numpy as np

from dent.RectangleObjects import RectangleObject
from dent.RenderStage import RenderStage
import dent.Texture

class GaussianBlurStage(RenderStage):
  def __init__(self, direction=np.array([1., 0.]), *args, **kwargs):
    kwargs['render_func'] = self.render
    super(GaussianBlurStage, self).__init__(*args, **kwargs)

    self._blur_rectangle_object = RectangleObject('gaussian')
    self._blur_rectangle_object.shader['colormap'] = dent.Texture.COLORMAP_NUM

    self.direction = direction


  def render(self, previous_stage, **kwargs):
    previous_stage.displayColorTexture.load()

    self._blur_rectangle_object.shader['direction'] = self.direction
    self._blur_rectangle_object.display()
