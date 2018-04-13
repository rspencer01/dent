import OpenGL.GL as gl
import os
import dent.assets
import numpy as np
import pyassimp
import Texture
import TextureManager
import Shaders
import transforms
import logging
import taskQueue
import threading
import ActionController
from dent.Mesh import Mesh
from dent.Material import Material
from collections import namedtuple
import Animation

MeshOptions = namedtuple("MeshOptions", ("has_bumpmap", "has_bones"))
MeshDatum = namedtuple("MeshDatum", ("name", "options", "mesh"))


class Object(object):

    def __init__(
        self,
        filename,
        name=None,
        scale=1,
        position=np.zeros(3),
        offset=np.zeros(3),
        angle=0.,
        will_animate=False,
        daemon=True,
    ):

        if name == None:
            name = os.path.basename(filename)

        if will_animate:
            daemon = False

        self.filename = filename
        self.directory = os.path.dirname(filename)
        self.name = name
        self.scene = None
        self.meshes = []
        self.meshes_per_material = {}
        self.renderIDs = {}
        self.scale = scale
        self.bones = {}
        self.bone_transforms = [np.eye(4, dtype=float) for _ in xrange(60)]
        self.action_controller = None
        self.will_animate = will_animate
        self.position = np.array(position, dtype=np.float32)
        self.last_unanimated_position = None
        if self.will_animate:
            self.offset = np.zeros(3)
        else:
            self.offset = np.array(offset, dtype=np.float32)
        self.direction = np.array((0, 0, 1), dtype=float)
        self.bidirection = np.array((1, 0, 0), dtype=float)
        self.angle = angle
        self.daemon = daemon

        self.shader = Shaders.getShader("general-noninstanced")
        self.shader["colormap"] = Texture.COLORMAP_NUM
        self.shader["normalmap"] = Texture.NORMALMAP_NUM
        self.shader["specularmap"] = Texture.SPECULARMAP_NUM

        self.bounding_box_min = np.zeros(3, dtype=float) + 1e10
        self.bounding_box_max = np.zeros(3, dtype=float) - 1e10

        if self.filename[-4:] == ".fbx":
            self.scale *= 0.01

        if self.daemon:
            thread = threading.Thread(target=self.loadFromFile)
            thread.setDaemon(True)
            thread.start()
        else:
            self.loadFromFile()

    def __del__(self):
        logging.info("Releasing object {}".format(self.name))
        # Release the pyassimp, as we no longer need it
        pyassimp.release(self.scene)

    def loadFromFile(self):
        """Loads the object from the disk.  Where possible, the dent asset library will
        use cached versions of meshes, materials and such forth."""

        logging.info("Loading object {} from {}".format(self.name, self.filename))

        material_names = dent.assets.getAsset(
            self.name + "-material-names", lambda: None
        )
        self.bones = dent.assets.getAsset(self.name + "-bones", lambda: {})
        mesh_info = dent.assets.getAsset(self.name + "-mesh_info", lambda: None)
        full_meshes = []
        if mesh_info is None or material_names is None:
            # Some of these are for static only and must be removed when doing bones.
            # This call is exceptionally slow.  Must we move to c?
            self.scene = pyassimp.load(
                self.filename,
                processing=pyassimp.postprocess.aiProcess_CalcTangentSpace
                | pyassimp.postprocess.aiProcess_Triangulate
                | pyassimp.postprocess.aiProcess_JoinIdenticalVertices
                | pyassimp.postprocess.aiProcess_LimitBoneWeights
                | pyassimp.postprocess.aiProcess_GenNormals,
            )
            mesh_info = []

            self.materials = {}
            for material in self.scene.materials:
                self.materials[material.properties[("name", 0)]] = Material()
                self.materials[material.properties[("name", 0)]].load_from_assimp(
                    material, self.directory
                )
                dent.assets.saveAsset(
                    self.name + "-material-" + material.properties[("name", 0)],
                    self.materials[material.properties[("name", 0)]],
                )
            material_names = self.materials.keys()
            dent.assets.saveAsset(self.name + "-material-names", material_names)

            def addNode(node, trans, node_info):
                newtrans = trans.dot(node.transformation)
                for msh in node.meshes:
                    full_meshes.append(
                        (
                            "{}-{}-{}".format(self.name, len(node_info), node.name),
                            msh,
                            newtrans,
                        )
                    )
                    node_info.append(
                        (
                            "{}-{}-{}".format(self.name, len(node_info), node.name),
                            None,
                            newtrans,
                        )
                    )
                for nod in node.children:
                    addNode(nod, newtrans, mesh_info)

            t = np.eye(4)
            addNode(self.scene.rootnode, t, mesh_info)

            dent.assets.saveAsset(self.name + "-mesh_info", mesh_info)

        if full_meshes:
            mesh_info = full_meshes
        for mesh in mesh_info:
            self.addMesh(*mesh)

        self.bones = dent.assets.getAsset(
            self.name + "-bones", lambda: self.bones, forceReload=True
        )

        self.materials = dict(
            [
                (
                    name,
                    dent.assets.getAsset(
                        self.name + "-material-" + name, type_hint=Material
                    ),
                )
                for name in material_names
            ]
        )
        for material in self.materials.values():
            material.load_textures()
            self.meshes_per_material[material.name] = []
        for mesh in self.meshes:
            self.meshes_per_material[mesh.mesh.material_name].append(mesh.mesh)

    def addMesh(self, name, assimp_mesh, trans):
        """Adds a mesh to this object.  This may be loaded from cache if possible."""
        logging.info("Loading mesh {}".format(name))
        options = MeshOptions(False, False)

        def load_mesh_from_assimp():
            mesh = Mesh(name, trans, self.offset, self.directory)
            mesh.load_from_assimp(assimp_mesh, self.directory, self.scene, self)
            return mesh

        mesh = dent.assets.getAsset(name, load_mesh_from_assimp, type_hint=Mesh)

        # Update the bounding box
        self.bounding_box_min = np.min(
            [self.bounding_box_min, np.min(mesh.data["position"], 0)], 0
        )
        self.bounding_box_max = np.max(
            [self.bounding_box_min, np.max(mesh.data["position"], 0)], 0
        )

        # Do skinning
        if self.will_animate:
            if len(self.bones) > 0:
                options = options._replace(has_bones=True)

        self.meshes.append(MeshDatum(name, options, mesh))

        taskQueue.addToMainThreadQueue(self.uploadMesh, (mesh,))

    def uploadMesh(self, mesh):
        self.renderIDs[mesh.name] = self.shader.setData(mesh.data, mesh.indices)
        logging.info("Loaded mesh {}".format(mesh.name))

    def update(self, time=0):
        if self.action_controller is not None:
            self.action_controller.update(time)

    def display(self):
        self.shader.load()
        t = np.eye(4, dtype=np.float32)
        t[2, 0:3] = self.direction
        t[0, 0:3] = self.bidirection
        # fmt: off
        t[0][0:3], t[2][0:3] = np.cos(self.angle) * t[0][0:3] + np.sin(self.angle) * t[2][0:3],\
                               np.cos(self.angle) * t[2][0:3] - np.sin(self.angle) * t[0][0:3]
        #fmt: on
        t[0:3, 0:3] *= self.scale
        if self.last_unanimated_position is not None:
            transforms.translate(
                t,
                self.last_unanimated_position[0],
                self.last_unanimated_position[1],
                self.last_unanimated_position[2],
            )
        else:
            transforms.translate(
                t, self.position[0], self.position[1], self.position[2]
            )
        self.shader["model"] = t

        if self.action_controller is not None:
            self.shader["bones"] = self.bone_transforms
            self.shader["hasSkinning"] = 1
        else:
            self.shader["hasSkinning"] = 0
        for material in self.materials.values():
          material.set_uniforms(self.shader)
          for mesh in self.meshes_per_material[material.name]:
            if mesh.name in self.renderIDs:
              self.shader.draw(gl.GL_TRIANGLES, self.renderIDs[mesh.name])

    def add_animation(self, filename):
        if self.action_controller is None:
            self.action_controller = ActionController.ActionController(self)

        def load_animation():
            animation = Animation.Animation()
            animation.load_from_file(filename,self.bones)
            return animation

        animation = dent.assets.getAsset(filename, load_animation, type_hint=Animation.Animation)
        self.action_controller.add_action(animation)

        self.last_unanimated_position = self.position

    def __repr__(self):
        return '<pmObject "{}">'.format(self.name)
