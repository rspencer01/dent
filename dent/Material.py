import StringIO
import logging
import os
import tarfile
import pyassimp
import pyassimp.material
import yaml
import numpy as np

import dent.Texture
import dent.TextureManager


def get_texture_filename(material, texture_type, directory):
    """Finds the filepath of a texture given the assimp material and the directory.

    This function looks for "dent-standard" texture locations, (the directory
    of the model, plus `<MATERIAL_NAME>.diff.png` etc. as well as any filenames
    mentioned in the material file.

    If no suitable filename can be found, None is returned.
    """
    dent_formats = {
        pyassimp.material.aiTextureType_DIFFUSE: "{}.diff.png",
        pyassimp.material.aiTextureType_NORMALS: "{}.norm.png",
        pyassimp.material.aiTextureType_SPECULAR: "{}.spec.png",
        pyassimp.material.aiTextureType_SHININESS: "{}.meta.png",
    }
    material_name = material.properties[("name", 0)]

    if texture_type in dent_formats:
        filename = os.path.join(
            directory, dent_formats[texture_type].format(material_name)
        )
        if os.path.exists(filename):
            return dent_formats[texture_type].format(material_name)

    if ("file", texture_type) in material.properties:
        filename = os.path.join(directory, material.properties[("file", texture_type)])
        if os.path.exists(filename):
            return material.properties[("file", texture_type)]

    logging.debug("Texture {} {} {} not found", directory, material_name, texture_type)


class Material(object):
    """Represents a material, with all the properties and textures required by shaders."""
    __slots__ = (
        "name",
        "directory",
        "diffuse_texture_file",
        "_diffuse_texture",
        "diffuse_tint",
        "normal_texture_file",
        "_normal_texture",
        "specular_texture_file",
        "_specular_texture",
        "specular_tint",
        "roughness_texture_file",
        "_roughness_texture",
        "roughness_tint",
        "metallic_texture_file",
        "_metallic_texture",
        "metallic_tint",
    )

    def __init__(self):
        for i in self.__slots__:
            setattr(self, i, None)

    def set_uniforms(self, shader):
        """Sets all the properties held in this material as uniforms in the shader."""
        shader["diffuse_tint"] = self.diffuse_tint
        shader["metallic_tint"] = self.metallic_tint
        shader["specular_tint"] = self.specular_tint
        shader["colormap"] = dent.Texture.COLORMAP_NUM
        shader["normalmap"] = dent.Texture.NORMALMAP_NUM
        shader["specularmap"] = dent.Texture.SPECULARMAP_NUM
        shader["metallicmap"] = dent.Texture.METALLICMAP_NUM
        shader["roughnessmap"] = dent.Texture.ROUGHNESSMAP_NUM
        self._diffuse_texture.load()
        self._normal_texture.load()
        self._specular_texture.loadAs(dent.Texture.SPECULARMAP)
        self._metallic_texture.loadAs(dent.Texture.METALLICMAP)

    def load_textures(self):
        if self.diffuse_texture_file:
            self._diffuse_texture = dent.TextureManager.get_texture(
                os.path.join(self.directory, self.diffuse_texture_file),
                dent.Texture.COLORMAP,
            )
        else:
            self._diffuse_texture = dent.Texture.getWhiteTexture()

        if self.normal_texture_file:
            self._normal_texture = dent.TextureManager.get_texture(
                os.path.join(self.directory, self.normal_texture_file),
                dent.Texture.NORMALMAP,
            )
        else:
            self._normal_texture = dent.Texture.getConstantNormalTexture()

        if self.specular_texture_file:
            self._specular_texture = dent.TextureManager.get_texture(
                os.path.join(self.directory, self.specular_texture_file),
                dent.Texture.SPECULARMAP,
            )
        else:
            self._specular_texture = dent.Texture.getWhiteTexture()

        if self.metallic_texture_file:
            self._metallic_texture = dent.TextureManager.get_texture(
                os.path.join(self.directory, self.metallic_texture_file),
                dent.Texture.METALLICMAP,
            )
        else:
            self._metallic_texture = dent.Texture.getWhiteTexture()

    def load_from_assimp(self, assimp_material, directory):
        # Load the texture filenames
        self.diffuse_texture_file = get_texture_filename(
            assimp_material, pyassimp.material.aiTextureType_DIFFUSE, directory
        )
        self.normal_texture_file = get_texture_filename(
            assimp_material, pyassimp.material.aiTextureType_NORMALS, directory
        ) or get_texture_filename(
            assimp_material, pyassimp.material.aiTextureType_HEIGHT, directory
        )
        self.specular_texture_file = get_texture_filename(
            assimp_material, pyassimp.material.aiTextureType_SPECULAR, directory
        )
        self.metallic_texture_file = get_texture_filename(
            assimp_material, pyassimp.material.aiTextureType_SHININESS, directory
        )
        self.roughness_texture_file = get_texture_filename(
            assimp_material, pyassimp.material.aiTextureType_SHININESS, directory
        )
        self.diffuse_tint = np.array(assimp_material.properties[("diffuse", 0)])
        self.specular_tint = np.linalg.norm(assimp_material.properties[("specular", 0)])
        self.metallic_tint = float(assimp_material.properties[("shininess", 0)])
        self.roughness_tint = self.specular_tint

        self.name = assimp_material.properties[("name", 0)]
        self.directory = directory

    @staticmethod
    def _dent_asset_load(datastore):
        """Loads this material from a dent asset datastore."""
        if "config" not in datastore.getnames():
            raise IOError()

        config = yaml.load(datastore.extractfile("config").read())
        material = Material()
        material.name = config["name"]
        material.directory = config["directory"]
        material.diffuse_texture_file = config["diffuse_texture_file"]
        material.normal_texture_file = config["normal_texture_file"]
        material.specular_texture_file = config["specular_texture_file"]
        material.metallic_texture_file = config["metallic_texture_file"]
        material.roughness_texture_file = config["roughness_texture_file"]
        material.diffuse_tint = config["diffuse_tint"]
        material.metallic_tint = config["metallic_tint"]
        material.specular_tint = config["specular_tint"]
        material.roughness_tint = config["roughness_tint"]
        material.load_textures()

        return material

    def _dent_asset_save(self, datastore):
        """Saves this material to a dent asset datastore."""
        config_buffer = StringIO.StringIO()
        config_buffer.write(
            yaml.dump(
                {
                    "name": self.name,
                    "directory": self.directory,
                    "diffuse_texture_file": self.diffuse_texture_file,
                    "normal_texture_file": self.normal_texture_file,
                    "specular_texture_file": self.specular_texture_file,
                    "metallic_texture_file": self.metallic_texture_file,
                    "roughness_texture_file": self.metallic_texture_file,
                    "diffuse_tint": self.diffuse_tint,
                    "metallic_tint": self.metallic_tint,
                    "specular_tint": self.metallic_tint,
                    "roughness_tint": self.metallic_tint,
                }
            )
        )
        config_buffer.flush()
        config_buffer.seek(0)
        config_header = tarfile.TarInfo("config")
        config_header.size = config_buffer.len
        datastore.addfile(config_header, config_buffer)
