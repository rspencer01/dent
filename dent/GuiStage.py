from dent.RenderStage import RenderStage
import OpenGL.GL as gl
import dent.messaging
import imgui
import imgui.integrations.opengl

class GuiStage(RenderStage):
  def __init__(self, *args, **kwargs):
    kwargs['render_func'] = self.render
    super(GuiStage, self).__init__(*args, **kwargs)
    self.renderer = imgui.integrations.opengl.ProgrammablePipelineRenderer()

    self.io = imgui.get_io()
    self.io.display_fb_scale = 1.,1.
    self.io.display_size = 1,1
    imgui.new_frame()

    self.io.delta_time = 1.0/60

    dent.messaging.add_handler('mouse_motion', self.mouse_motion_handler)
    dent.messaging.add_handler('mouse', self.mouse_handler)


  def render(self, width, height, previous_stage):
    self.io.display_size = width, height

    imgui.new_frame()
    self.make_gui(width, height)
    imgui.render()

  def mouse_handler(self, button, state, x, y):
    # Mouse down
    if state == 0:
      self.io.mouse_down[button] = True
    else:
      self.io.mouse_down[button] = False

  def mouse_motion_handler(self, x, y):
    self.io.mouse_pos = x,y

  def load(self, width, height, offsetx=0, offsety=0, clear=None):
    """Loads the render stage's buffers, clears them and sets the viewport.

    The depth buffer will always be cleared, but the color buffer is cleared
    only if the `clear` argument is true (default).

    If the stage is "final", the screen buffer will be loaded."""
    if not self.final_stage:
      gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.displayFBO)
    else:
      gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    self.width = width
    self.height = height
    gl.glViewport(offsetx, offsety, width, height)
