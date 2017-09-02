from RenderStage import RenderStage

class RenderPipeline(object):
  def __init__(self, stages=[]):
    self.stages = stages

  def run(self, width, height):
    previous_stage = None
    for stage in self.stages:
      if stage.enabled:
        stage.load(width, height)
        if stage.render:
          stage.render(width=width, height=height, previous_stage=previous_stage)
        previous_stage = stage
