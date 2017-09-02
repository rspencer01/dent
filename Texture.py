import OpenGL.GL as gl
import numpy as np
import scipy.ndimage
import Image
import logging
import sys
import taskQueue
import assets
import args

HEIGHTMAP = gl.GL_TEXTURE0
HEIGHTMAP_NUM = 0
SHADOWS1 = gl.GL_TEXTURE1
SHADOWS1_NUM = 1
SHADOWS2 = gl.GL_TEXTURE2
SHADOWS2_NUM = 2
SHADOWS3 = gl.GL_TEXTURE3
SHADOWS3_NUM = 3
NOISE = gl.GL_TEXTURE4
NOISE_NUM = 4
BUMPMAP = gl.GL_TEXTURE5
BUMPMAP_NUM = 5
COLORMAP = gl.GL_TEXTURE6
COLORMAP_NUM = 6
DEPTHMAP = gl.GL_TEXTURE7
DEPTHMAP_NUM = 7
COLORMAP2 = gl.GL_TEXTURE8
COLORMAP2_NUM = 8
COLORMAP3 = gl.GL_TEXTURE9
COLORMAP3_NUM = 9
FOLIAGEMAP = gl.GL_TEXTURE10
FOLIAGEMAP_NUM = 10
EARTHMAP = gl.GL_TEXTURE11
EARTHMAP_NUM = 11
OPTICAL_DEPTHMAP = gl.GL_TEXTURE12
OPTICAL_DEPTHMAP_NUM = 12
NIGHTSKY = gl.GL_TEXTURE13
NIGHTSKY_NUM = 13
NORMALMAP = gl.GL_TEXTURE14
NORMALMAP_NUM = 14
PAGE_TABLE = gl.GL_TEXTURE15
PAGE_TABLE_NUM = 15
PAGED_TEXTURE_1 = gl.GL_TEXTURE16
PAGED_TEXTURE_1_NUM = 16
PAGED_TEXTURE_2 = gl.GL_TEXTURE17
PAGED_TEXTURE_2_NUM = 17
PAGED_TEXTURE_3 = gl.GL_TEXTURE18
PAGED_TEXTURE_3_NUM = 18
SPECULARMAP = gl.GL_TEXTURE19
SPECULARMAP_NUM = 19

textureUnits = gl.glGetIntegerv(gl.GL_MAX_TEXTURE_IMAGE_UNITS)
logging.info("Found {} texture units".format(textureUnits))
if textureUnits < 32:
  logging.fatal("Insufficient texture units.  Require 32, have {}".format(textureUnits))
  sys.exit(1)

activeTexture = None

class Texture:
  def __init__(self, type, nonblocking=False, internal_format=gl.GL_RGBA32F):
    """Creates a new texture of the given type.  If nonblocking is specified
    true, the creation of the texture handle will be added to the GPU queue.  If
    this is done, all texture loads _must_ occur after the handle has been
    acquired."""
    self.textureType =  type
    self.id = None
    self._data = None
    self.internal_format = internal_format

    if nonblocking:
      taskQueue.addToMainThreadQueue(self.initialise)
    else:
      self.initialise()


  def initialise(self):
    self.id = gl.glGenTextures(1)
    self.load()

    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)

    logging.info("New texture {}".format(self.id))


  def loadData(
      self,
      data,
      width=None,
      height=None,
      type=gl.GL_FLOAT,
      keep_copy=False,
      make_mipmap=True):
    """Loads data to the GPU.  Parameter `data` may either be a numpy array of
    shape `(width,height,4)` or `None` (in which case `width` and `height` must
    be specified)."""
    if data is not None:
      if data.nbytes > 1024**6:
        logging.warn("Texture {} is of size {:.2f}M (too big)".format(self.id, data.nbytes/1024**2))
        if data.nbytes < 1024**2 * 10:
          logging.warn("Resizing {}".format(self.id))
          data = scipy.ndimage.zoom(data, (0.5, 0.5, 1))

    if width == None:
      width = data.shape[0]
    if height == None:
      height = data.shape[1]
    self.load()
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0 ,self.internal_format, width, height, 0, gl.GL_RGBA, type, data)
    if keep_copy:
      self._data = data.copy()
    if make_mipmap:
      self.makeMipmap()


  def makeMipmap(self):
    self.load()
    gl.glGenerateMipmap(gl.GL_TEXTURE_2D)


  def load(self):
    self.loadAs(self.textureType)


  def loadAs(self, type):
    global activeTexture
    if type != activeTexture:
      gl.glActiveTexture(type)
      activeTexture = type
    gl.glBindTexture(gl.GL_TEXTURE_2D, self.id)


  def getData(self):
    self.load()
    return gl.glGetTexImage(gl.GL_TEXTURE_2D,0,gl.GL_RGBA,gl.GL_FLOAT)


  def saveToFile(self,fileName):
    np.save(fileName,self.getData())


  def loadFromFile(self,fileName):
    data = np.load(fileName)
    self.loadData(data)
    del data


  def loadFromImage(self, filename, daemon=True):
    def readFromFile(filename):
      teximag = Image.open(filename)
      data = np.array(teximag.getdata()).astype(np.float32)

      ## Make this a 4 color file
      if (data.shape[1] != 4):
        add = np.zeros((data.shape[0],1),dtype=np.float32)+256
        data = np.append(data, add, axis=1)

      data = data.reshape(teximag.size[0], teximag.size[1], 4)

      return data

    data = assets.getAsset(filename, readFromFile, (filename,), args.args.reload_textures)

    def uploadToGPU(data):
      logging.info("Uploading texture {} ({})".format(self.id, filename))
      self.loadData(data/256)

    # We have now loaded the image data.  We need to upload it to the GPU.
    # Either we do this on the main thread, or if we are not using a daemon
    # style, we are the main thread and we must do it now.
    if daemon:
      taskQueue.addToMainThreadQueue(uploadToGPU, (data,))
    else:
      uploadToGPU(data)


  def read(self, x, y, interpolate=True):
    assert self._data is not None

    x = np.fmod(x, 1)
    if x < 0: x += 1
    if x >= 1: x -= 1
    y = np.fmod(y, 1)
    if y < 0: y += 1
    if y >= 1: y -= 1

    y = float(y) * (self._data.shape[0]) - 0.5
    x = float(x) * (self._data.shape[1]) - 0.5
    if x > self._data.shape[1] -2:
      x = self._data.shape[1] -2
    if y > self._data.shape[0] -2:
      y = self._data.shape[0] -2

    f1 = (x-int(x))
    f2 = (y-int(y))

    if not interpolate:
      f1 = 1 if f1 > 0.5 else 0
      f2 = 1 if f2 > 0.5 else 0

    r = (self._data[int(y),int(x)] * (1-f2) + self._data[int(y+1),int(x)] * f2) * (1-f1)+\
        (self._data[int(y),int(x+1)] * (1-f2) + self._data[int(y+1),int(x+1)] * f2) * f1
    return r


  def __del__(self):
    logging.info("Freeing texture {}".format(self.id))
    gl.glDeleteTextures(self.id)


whiteTexture = None
blackTexture = None

def getWhiteTexture():
  global whiteTexture
  if whiteTexture is None:
    whiteTexture = Texture(COLORMAP)
    whiteTexture.loadData(np.ones((1,1,4),dtype=np.float32))
  return whiteTexture

def getBlackTexture():
  global blackTexture
  if blackTexture is None:
    blackTexture = Texture(COLORMAP)
    blackTexture.loadData(np.zeros((1,1,4),dtype=np.float32))
  return blackTexture
