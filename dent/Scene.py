from dent.Camera import Camera
from dent.RenderPipeline import RenderPipeline
from dent.RenderStage import RenderStage

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
