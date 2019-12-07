import numpy as np
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
    """Holds the data for a single mesh.

    This object describes, in memory, the vertex data for a particular mesh of a
    model.  Mesh loading from pyassimp meshes is also implemented.

    In general, this object should always belong to an Object, be loaded from a
    file and not be created by the game.  It is suitable to be saved to disk
    using the dent asset manager.
    """

    def __init__(self, name, transform=np.eye(4), offset=np.zeros(3), directory=""):
        self.name = name
        self.directory = directory
        self.data = None
        self.indices = None
        self._transform = transform
        self.offset = offset
        self.material_name = None

    def load_from_assimp(self, assimp_mesh, directory, scene, parent):
        """Load this mesh from an assimp mesh."""
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
        vertex_positions = assimp_mesh.vertices
        add = np.ones((vertex_positions.shape[0], 1), dtype=np.float32)
        vertex_positions = np.append(vertex_positions, add, axis=1)
        # Get the vertex normals and add a w=1 component
        vertex_normals = assimp_mesh.normals
        add = np.zeros((vertex_normals.shape[0], 1), dtype=np.float32)
        vertex_normals = np.append(vertex_normals, add, axis=1)

        tinvtrans = np.linalg.inv(self._transform).transpose()
        # Transform all the vertex positions.
        for i in range(len(vertex_positions)):
            vertex_positions[i] = self._transform.dot(vertex_positions[i])
            vertex_normals[i] = tinvtrans.dot(vertex_normals[i])
        # Splice correctly, killing last components
        vertex_positions = vertex_positions[:, 0:3] - self.offset
        vertex_normals = vertex_normals[:, 0:3]

        vertex_uvs = assimp_mesh.texturecoords[0][:, [0, 1]]
        vertex_uvs[:, 1] = 1 - vertex_uvs[:, 1]

        # Set the data
        self.data["position"] = vertex_positions
        self.data["normal"] = vertex_normals
        self.data["textcoord"] = vertex_uvs
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
                        n,
                        get_node_parent(scene, bone.name).name,
                        bone.offsetmatrix,
                    )
                    nn = n
                else:
                    nn = parent.bones[bone.name][0]
                for relationship in bone.weights:
                    bone_vec_number = 0
                    for i in range(3):
                        if (
                            self.data["weights"][relationship.vertexid][bone_vec_number]
                            > 0
                        ):
                            bone_vec_number += 1
                        else:
                            break

                    self.data["weights"][relationship.vertexid][
                        bone_vec_number
                    ] = relationship.weight
                    self.data["bone_ids"][relationship.vertexid][bone_vec_number] = nn

        self.material_name = assimp_mesh.material.properties[("name", 0)]

    def union(self, other) -> "Mesh":
        """Construct the union of this mesh with another.

        Currently this forgets all materials etc. and is simply an action on sets of
        triangles.
        """
        mesh = Mesh("{}|{}".format(self.name, other.name))
        mesh.data = np.concatenate((self.data, other.data))
        mesh.indices = np.concatenate((self.indices, other.indices + len(self.data)))
        return mesh

    @staticmethod
    def _dent_asset_load(datastore) -> "Mesh":
        if "config" not in datastore.getnames() or "data" not in datastore.getnames():
            raise IOError()

        config = yaml.safe_load(datastore.extractfile("config").read())
        mesh = Mesh(
            config["name"],
            np.array(config["transform"]).reshape((4, 4)),
            np.array(config["offset"]),
            config["directory"],
        )
        mesh.indices = np.array(config["indices"])
        mesh.material_name = config["material_name"]
        array_file = io.BytesIO()
        array_file.write(datastore.extractfile("data").read())
        array_file.seek(0)
        mesh.data = np.load(array_file)
        return mesh

    def _dent_asset_save(self, datastore):
        """Save the image in this texture to a dent asset datastore."""
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
                    "transform": self._transform.tolist(),
                    "offset": self.offset.tolist(),
                    "indices": self.indices.tolist(),
                    "material_name": self.material_name,
                }
            ).encode("ascii")
        )
        config_buffer.flush()
        config_header = tarfile.TarInfo("config")
        config_header.size = config_buffer.getbuffer().nbytes
        config_buffer.seek(0)
        datastore.addfile(config_header, config_buffer)
