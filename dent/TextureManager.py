import Texture
import logging

_LOADED_TEXTURES = {}

def get_texture(path, type):
  if (path, type) not in _LOADED_TEXTURES:
    logging.info("Loading texture from {}".format(path))
    texture = Texture.Texture(type)
    texture.loadFromImage(path)
    _LOADED_TEXTURES[(path, type)] = texture
  return _LOADED_TEXTURES[(path, type)]
