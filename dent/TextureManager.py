import logging
import dent.Texture
import dent.assets

_LOADED_TEXTURES = {}


def get_texture(path, texture_type):
    if (path, texture_type) not in _LOADED_TEXTURES:
        logging.info("Loading type {} texture from {}".format(texture_type, path))

        def get_new_texture():
            texture = dent.Texture.Texture(texture_type)
            texture.loadFromImage(path)
            return texture

        _LOADED_TEXTURES[(path, texture_type)] = dent.assets.getAsset(
            path, get_new_texture, type_hint=dent.Texture.Texture
        )
    return _LOADED_TEXTURES[(path, texture_type)]
