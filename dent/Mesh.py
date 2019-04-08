import logging
import os
import numpy as np
import dent.TextureManager
import dent.Texture
import yaml
import io
import tarfile


def get_node_parent(scene, name):

    def dfs(node, parent):
        if node.name == name:
            return parent

        for i in node.children:
            a = dfs(i, node)
            if a:
                return a

        return None

    return dfs(scene.rootnode, "")


class Mesh(object):
    """ Holds the data for a single mesh.

    This object describes, in memory, the vertex data for a particular mesh of a
    model.  Mesh loading from pyassimp meshes is also implemented.

    In general, this object should always belong to an Object, be loaded from a
    file and not be created by the game.  It is suitable to be saved to disk
    using the dent asset manager."""

    def __init__(self, name, transform, offset, directory):
        self.name = name
        self.directory = directory
        self.data = None
        self.indices = None
        self.transform = transform
        self.offset = offset
        self.material_name = None

    def load_from_assimp(self, assimp_mesh, directory, scene, parent):
        self.data = np.zeros(
            len(assimp_mesh.vertices),
            dtype=[
                ("position", np.float32, 3),
                ("normal", np.float32, 3),
                ("textcoord", np.float32, 2),
                ("tangent", np.float32, 3),
                ("bitangent", np.float32, 3),
                ("bone_ids", np.int32, 4),
                ("weights", np.float32, 4),
            ],
        )

        # Get the vertex positions and add a w=1 component
        vertPos = assimp_mesh.vertices
        add = np.ones((vertPos.shape[0], 1), dtype=np.float32)
        vertPos = np.append(vertPos, add, axis=1)
        # Get the vertex normals and add a w=1 component
        vertNorm = assimp_mesh.normals
        add = np.zeros((vertNorm.shape[0], 1), dtype=np.float32)
        vertNorm = np.append(vertNorm, add, axis=1)

        tinvtrans = np.linalg.inv(self.transform).transpose()
        # Transform all the vertex positions.
        for i in range(len(vertPos)):
            vertPos[i] = self.transform.dot(vertPos[i])
            vertNorm[i] = tinvtrans.dot(vertNorm[i])
        # Splice correctly, killing last components
        vertPos = vertPos[:, 0:3] - self.offset
        vertNorm = vertNorm[:, 0:3]

        vertUV = assimp_mesh.texturecoords[0][:, [0, 1]]
        vertUV[:, 1] = 1 - vertUV[:, 1]

        # Set the data
        self.data["position"] = vertPos
        self.data["normal"] = vertNorm
        self.data["textcoord"] = vertUV
        self.data["tangent"] = assimp_mesh.tangents
        self.data["bone_ids"] = 59
        self.data["bitangent"] = assimp_mesh.bitangents
        self.data["weights"] = 0

        # Get the triangle indices in a flat array.
        self.indices = assimp_mesh.faces.reshape((-1,))

        if len(assimp_mesh.bones) > 0:
            for bone in assimp_mesh.bones:
                n = len(parent.bones)
                if bone.name not in parent.bones:
                    parent.bones[bone.name] = (
                        n, get_node_parent(scene, bone.name).name, bone.offsetmatrix
                    )
                    nn = n
                else:
                    nn = parent.bones[bone.name][0]
                for relationship in bone.weights:
                    bone_vec_number = 0
                    for i in range(3):
                        if self.data["weights"][relationship.vertexid][
                            bone_vec_number
                        ] > 0:
                            bone_vec_number += 1
                        else:
                            break

                    self.data["weights"][relationship.vertexid][
                        bone_vec_number
                    ] = relationship.weight
                    self.data["bone_ids"][relationship.vertexid][bone_vec_number] = nn

        self.material_name = assimp_mesh.material.properties[("name", 0)]

    @staticmethod
    def _dent_asset_load(datastore):
        if "config" not in datastore.getnames() or "data" not in datastore.getnames():
            raise IOError()

        config = yaml.load(datastore.extractfile("config").read())
        mesh = Mesh(
            config["name"], config["transform"], config["offset"], config["directory"]
        )
        mesh.indices = config["indices"]
        mesh.material_name = config["material_name"]
        mesh.data = np.load(datastore.extractfile("data"))
        return mesh

    def _dent_asset_save(self, datastore):
        """Saves the image in this texture to a dent asset datastore."""
        data_buffer = io.BytesIO()
        np.save(data_buffer, self.data)
        data_header = tarfile.TarInfo("data")
        data_header.size = data_buffer.getbuffer().nbytes
        data_buffer.seek(0)
        datastore.addfile(data_header, data_buffer)

        config_buffer = io.BytesIO()
        config_buffer.write(
            yaml.dump(
                {
                    "name": self.name,
                    "directory": self.directory,
                    "transform": self.transform,
                    "offset": self.offset,
                    "indices": self.indices,
                    "material_name": self.material_name,
                }
            ).encode('ascii')
        )
        config_buffer.flush()
        config_header = tarfile.TarInfo("config")
        config_header.size = config_buffer.getbuffer().nbytes
        config_buffer.seek(0)
        datastore.addfile(config_header, config_buffer)
