import logging
import dent.Texture

_LOADED_TEXTURES = {}


def get_texture(path, texture_type):
    if (path, texture_type) not in _LOADED_TEXTURES:
        logging.info("Loading type {} texture from {}".format(texture_type, path))
        texture = dent.Texture.Texture(texture_type)
        texture.loadFromImage(path)
        _LOADED_TEXTURES[(path, texture_type)] = texture
    return _LOADED_TEXTURES[(path, texture_type)]
