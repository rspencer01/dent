import logging
import OpenGL.GL as gl
import OpenGL.GL.framebufferobjects as glfbo

import dent.Texture

class RenderStage(object):
  def __init__(
      self,
      render_func=None,
      final_stage=False,
      depth_only=False,
      clear_depth=True):
    """Constructs a render stage.  If the state is 'final', then rendering to it
    will render to the default buffer of id 0."""
    self.final_stage = final_stage
    self.width = None
    self.height = None
    self.render = render_func
    self.clear_depth = clear_depth
    self.enabled = True
    self.textures = []
    if not final_stage:
      self._create_fbos(depth_only)


  def load(self, width, height, offsetx=0, offsety=0, clear=None):
    """Loads the render stage's buffers, clears them and sets the viewport.

    The depth buffer will always be cleared, but the color buffer is cleared
    only if the `clear` argument is true (default).

    If the stage is "final", the screen buffer will be loaded."""
    if not self.final_stage:
      gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.displayFBO)
    else:
      gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    if clear is None:
      clear = self.clear_depth
    if clear:
      gl.glClear(gl.GL_DEPTH_BUFFER_BIT | gl.GL_COLOR_BUFFER_BIT)
    else:
      gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

    self.width = width
    self.height = height
    gl.glViewport(offsetx, offsety, width, height)


  def reshape(self, width, height=None):
    """Change the size of the textures in this stage.

    If height is None, it defaults to the provided width."""
    if self.final_stage:
      return

    if height is None:
      height = width

    for texture in self.textures:
      texture.loadData(None, width=width, height=height)

    self.displayDepthTexture.load()
    gl.glTexImage2D(
        gl.GL_TEXTURE_2D,
        0,
        gl.GL_DEPTH_COMPONENT32,
        width,
        height,
        0,
        gl.GL_DEPTH_COMPONENT,
        gl.GL_FLOAT,
        None)

    self.width = width
    self.height = height


  def _create_fbos(self, depth_only):
    self.displayFBO = gl.glGenFramebuffers(1)

    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.displayFBO)

    if not depth_only:
      self.displayColorTexture = dent.Texture.Texture(dent.Texture.COLORMAP)
      gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

      self.displaySecondaryColorTexture = dent.Texture.Texture(dent.Texture.COLORMAP2)
      gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

      self.displayAuxColorTexture = dent.Texture.Texture(dent.Texture.COLORMAP3)
      gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
      self.textures = [self.displayColorTexture, self.displaySecondaryColorTexture, self.displayAuxColorTexture]

    self.displayDepthTexture = dent.Texture.Texture(dent.Texture.DEPTHMAP)
    self.displayDepthTexture.load()
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_COMPARE_FUNC, gl.GL_LEQUAL)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_COMPARE_MODE, gl.GL_NONE)

    self.reshape(1)

    gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, self.displayDepthTexture.id, 0)
    if not depth_only:
      gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, self.displayColorTexture.id, 0)
      gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT1, self.displaySecondaryColorTexture.id, 0)
      gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT2, self.displayAuxColorTexture.id, 0)
      gl.glDrawBuffers(3, [gl.GL_COLOR_ATTACHMENT0, gl.GL_COLOR_ATTACHMENT1, gl.GL_COLOR_ATTACHMENT2])
    else:
      gl.glDrawBuffers(gl.GL_NONE)
    glfbo.checkFramebufferStatus()


  def __del__(self):
    """When the stage is deleted, we must get rid of any GPU resources we have
    requested."""
    logging.info("Deleting render stage %s", self)
    gl.glDeleteFramebuffers(1, [self.displayFBO])
