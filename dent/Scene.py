from dent.Camera import MouseControlledCamera
from dent.RenderPipeline import RenderPipeline
from dent.RenderStage import RenderStage
from dent.PhongLightingStage import PhongLightingStage


class Scene(object):

    def __init__(self):
        self.camera = MouseControlledCamera()
        self.renderPipeline = RenderPipeline(
            [RenderStage(render_func=self.display, final_stage=True)]
        )
        self._objects = []

    def render(self, windowWidth, windowHeight):
        self.renderPipeline.run(windowWidth, windowHeight)

    def display(self, **kwargs):
        self.camera.render()
        for obj in self._objects:
            obj.display()


class DeferredRenderScene(Scene):

    def __init__(self, phong_final=True):
        self.camera = MouseControlledCamera()
        self.renderPipeline = RenderPipeline(
            [
                RenderStage(render_func=self.display),
                PhongLightingStage(final_stage=phong_final),
            ]
        )
        self.lighting_stage = self.renderPipeline.stages[-1]
