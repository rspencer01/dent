import Camera
from RenderPipeline import RenderPipeline

class Scene(object):
  def __init__(self):
    self.camera = Camera.Camera()
    self.renderPipeline = RenderPipeline()

  def render(self, windowWidth, windowHeight):
    self.renderPipeline.run(windowWidth, windowHeight)
