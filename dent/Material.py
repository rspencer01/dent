import os
import dent.Texture
import dent.TextureManager


class Material(object):
    """Represents a material, with all the properties and textures required by shaders."""

    def __init__(self):
        self.name = None
        self.directory = None
        self.diffuse_texture_file = None
        self.normal_texture_file = None
        self.specular_texture_file = None
        self.diffuse_texture = None
        self.normal_texture = None
        self.specular_texture = None
        self.material_diffuse_color = None

    def set_uniforms(self, shader):
        shader["diffuse_tint"] = self.material_diffuse_color
        self.diffuse_texture.load()
        if self.normal_texture:
            self.normal_texture.load()
        self.specular_texture.load()

    def load_textures(self):
        if self.diffuse_texture_file:
            self.diffuse_texture = dent.TextureManager.get_texture(
                os.path.join(self.directory, self.diffuse_texture_file),
                dent.Texture.COLORMAP,
            )
        else:
            self.diffuse_texture = dent.Texture.getWhiteTexture()

        if self.normal_texture_file:
            self.normal_texture = dent.TextureManager.get_texture(
                os.path.join(self.directory, self.normal_texture_file),
                dent.Texture.NORMALMAP,
            )
        if self.specular_texture_file:
            self.specular_texture = dent.TextureManager.get_texture(
                os.path.join(self.directory, mesh.specular_texture_file),
                dent.Texture.SPECULARMAP,
            )
        else:
            self.specular_texture = dent.Texture.getBlackTexture()
            self.specular_texture.textureType = dent.Texture.SPECULARMAP

