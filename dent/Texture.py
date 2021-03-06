import io
import logging
import sys
import tarfile

import OpenGL.GL as gl
import imageio
import numpy as np
import scipy.ndimage
import yaml

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
SSAOMAP = gl.GL_TEXTURE20
SSAOMAP_NUM = 20
METALLICMAP = gl.GL_TEXTURE21
METALLICMAP_NUM = 21
ROUGHNESSMAP = gl.GL_TEXTURE22
ROUGHNESSMAP_NUM = 22
IRRADIENCEMAP = gl.GL_TEXTURE23
IRRADIENCEMAP_NUM = 23


def initialise():
    textureUnits = gl.glGetIntegerv(gl.GL_MAX_TEXTURE_IMAGE_UNITS)
    logging.info("Found {} texture units".format(textureUnits))
    if textureUnits < 32:
        logging.fatal(
            "Insufficient texture units.  Require 32, have {}".format(textureUnits)
        )
        sys.exit(1)


activeTexture = None

texture_id_pool = set()


def get_texture_id():
    """Obtains an unused texture id from the graphics library.

    This function must be run on the OpenGL thread."""
    if len(texture_id_pool) == 0:
        texture_id_pool.update(list(gl.glGenTextures(10)))
        logging.info("Requested 10 new textures")
    return texture_id_pool.pop()


class Texture(object):

    def __init__(self, type, internal_format=gl.GL_RGBA32F):
        """Creates a new texture of the given type.  If nonblocking is specified
        true, the creation of the texture handle will be added to the GPU queue.  If
        this is done, all texture loads _must_ occur after the handle has been
        acquired."""
        self.textureType = type
        self.id = None
        self._data = None
        self.width = 0
        self.height = 0
        self.internal_format = internal_format

        self.initialise()

    def initialise(self):
        """This function must be run on the main thread."""
        self.id = get_texture_id()
        self.load()

        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(
            gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR
        )

        logging.debug("New texture in ID {}".format(self.id))

    def loadData(
        self,
        data,
        width=None,
        height=None,
        type=gl.GL_FLOAT,
        keep_copy=False,
        make_mipmap=True,
    ):
        """Loads data to the GPU.  Parameter `data` may either be a numpy array of
        shape `(width,height,4)` or `None` (in which case `width` and `height` must
        be specified)."""
        if data is not None:
            if data.nbytes > 1024 ** 6:
                logging.warn(
                    "Texture {} is of size {:.2f}M (too big)".format(
                        self.id, data.nbytes / 1024 ** 2
                    )
                )
                if data.nbytes < 1024 ** 2 * 10:
                    logging.warn("Resizing {}".format(self.id))
                    data = scipy.ndimage.zoom(data, (0.5, 0.5, 1))

        if width == None:
            width = data.shape[0]
        if height == None:
            height = data.shape[1]

        self.width = width
        self.height = height

        self.load()
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            self.internal_format,
            width,
            height,
            0,
            gl.GL_RGBA,
            type,
            data,
        )

        if keep_copy:
            self._data = data.copy()
        if make_mipmap:
            self.makeMipmap()

    def makeMipmap(self):
        """Constructs all the mipmap levels for the texture.

        This invokes a GPU-based computation of all mipmap levels, and should
        be invoked, for example, when the texture has been rendered to.

        However, it does invoke a substantial time penalty, and so should not
        be used if mip levels will not be needed.  """
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
        return gl.glGetTexImage(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, gl.GL_FLOAT)

    def loadFromFile(self, fileName):
        data = np.load(fileName)
        self.loadData(data)
        del data

    def loadFromImage(self, filename):
        """Load this texture from an image file on disk.

        This uses the ``imageio`` library, and should therefore be able to
        handle nearly any type of image file format.  The image is immediately
        uploaded to the GPU to be ready for binding.

        Args:
            filename (str): Path to the image file (``.bmp``, ``.png`` etc)
        """
        data = imageio.imread(filename).astype(float)
        data = data.reshape((data.shape[1], data.shape[0], -1))

        # Make this a rgba file
        if (data.shape[2] != 4):
            add = np.ones((data.shape[0], data.shape[1], 1)) * 255
            data = np.append(data, add, axis=2)

        logging.info("Loaded texture %d from file %s", self.id, filename)
        self.loadData(data / 255)

    def read(self, x, y, interpolate=True):
        assert self._data is not None

        x = np.fmod(x, 1)
        if x < 0:
            x += 1
        if x >= 1:
            x -= 1
        y = np.fmod(y, 1)
        if y < 0:
            y += 1
        if y >= 1:
            y -= 1

        y = float(y) * (self._data.shape[0]) - 0.5
        x = float(x) * (self._data.shape[1]) - 0.5
        if x > self._data.shape[1] - 2:
            x = self._data.shape[1] - 2
        if y > self._data.shape[0] - 2:
            y = self._data.shape[0] - 2

        f1 = (x - int(x))
        f2 = (y - int(y))

        if not interpolate:
            f1 = 1 if f1 > 0.5 else 0
            f2 = 1 if f2 > 0.5 else 0

        # fmt: off
        r = np.interp(f1, [0, 1], [
                np.interp(f2,
                    [0, 1],
                    [
                      self._data[int(y), int(x)],
                      self._data[int(y + 1), int(x)],
                    ],
                ),
                np.interp(f2,
                    [0, 1],
                    [
                        self._data[int(y), int(x + 1)],
                        self._data[int(y + 1), int(x + 1)],
                    ],
                ),
            ],
        )
        #fmt: on
        return r

    def __del__(self):
        logging.info("Freeing texture {}".format(self.id))
        texture_id_pool.update([self.id])

    @staticmethod
    def _dent_asset_load(datastore):
        if "config" not in datastore.getnames() or "data" not in datastore.getnames():
            raise IOError()

        config = yaml.load(datastore.extractfile("config").read())
        texture = Texture(config["type"], internal_format=config["format"])
        data = np.safe_load(datastore.extractfile("data"))
        texture.loadData(data)
        return texture

    def _dent_asset_save(self, datastore):
        """Saves the image in this texture to a dent asset datastore."""
        data_buffer = io.BytesIO()
        np.save(data_buffer, self.getData())
        data_header = tarfile.TarInfo("data")
        data_header.size = data_buffer.getbuffer().nbytes
        data_buffer.seek(0)
        datastore.addfile(data_header, data_buffer)

        config_buffer = io.BytesIO()
        config_buffer.write(
            yaml.dump({"type": self.textureType, "format": self.internal_format}).encode('ascii')
        )
        config_header = tarfile.TarInfo("config")
        config_header.size = config_buffer.getbuffer().nbytes
        config_buffer.seek(0)
        datastore.addfile(config_header, config_buffer)


whiteTexture = None
blackTexture = None
blueTexture = None
constantNormalTexture = None


def getWhiteTexture():
    global whiteTexture
    if whiteTexture is None:
        whiteTexture = Texture(COLORMAP)
        whiteTexture.loadData(np.ones((1, 1, 4), dtype=np.float32))
    return whiteTexture


def getBlackTexture():
    global blackTexture
    if blackTexture is None:
        blackTexture = Texture(COLORMAP)
        blackTexture.loadData(np.zeros((1, 1, 4), dtype=np.float32))
    return blackTexture


def getBlueTexture():
    global blueTexture
    if blueTexture is None:
        blueTexture = Texture(NORMALMAP)
        blueTexture.loadData(np.array([[[0, 0, 1, 1]]], dtype=np.float32))
    return blueTexture


def getConstantNormalTexture():
    global constantNormalTexture
    if constantNormalTexture is None:
        constantNormalTexture = Texture(NORMALMAP)
        constantNormalTexture.loadData(np.array([[[0.5, 0.5, 1, 1]]], dtype=np.float32))
    return constantNormalTexture
