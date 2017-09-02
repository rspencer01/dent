import Shaders
import numpy as np
import OpenGL.GL as gl
import Texture

class RectangleObject(object):
  def __init__(self, shader_name):
    self.shader = Shaders.getShader(shader_name)

    data = np.zeros(4, dtype=[("position", np.float32, 3)])
    data['position'] = [(-1, -1, 0.999999), (-1, 1, 0.999999), (1, -1, 0.999999), (1, 1, 0.999999)]
    I = [0, 2, 1, 1, 2, 3]
    indices = np.array(I, dtype=np.int32)

    self.renderID = self.shader.setData(data, indices)

    self.position = np.array([0.5, 0.5])
    self.width = 1.
    self.height = 1.

  def display(self):
    model = np.eye(3, dtype=np.float32)
    model[0,0] = self.width
    model[1,1] = self.height
    model[2,:2] = (self.position - 0.5)*2
    self.shader['model'] = model
    self.shader.draw(gl.GL_TRIANGLES, self.renderID, 1)


class BlankImageObject(RectangleObject):
  def __init__(self, r=1., g=1., b=1.):
    super(BlankImageObject, self).__init__('image')
    self.shader['colormap'] = Texture.COLORMAP_NUM
    self.r = r
    self.g = g
    self.b = b

  def display(self):
    Texture.getWhiteTexture().load()
    self.shader['color'] = np.array([self.r, self.g, self.b])
    super(BlankImageObject, self).display()


class ImageObject(RectangleObject):
  def __init__(self, imagePath):
    super(ImageObject, self).__init__('image')
    self.picture = Texture.Texture(Texture.COLORMAP)
    self.picture.loadFromImage(imagePath)
    self.shader['colormap'] = Texture.COLORMAP_NUM

  def display(self):
    self.picture.load()
    self.shader['color'] = np.array([1.,1.,1.])
    super(ImageObject, self).display()
