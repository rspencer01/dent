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
from collections import namedtuple
import Animation

MeshOptions = namedtuple("MeshOptions", ("has_bumpmap", "has_bones"))
MeshDatum = namedtuple("MeshDatum", ("name", "data", "indices", "options", "mesh"))


def getOptionNumber(meshOptions):
  ans = 0
  for i, v in enumerate(meshOptions):
    if v:
      ans += 2 ** i
  return ans


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
    self.renderIDs = []
    self.scale = scale
    self.bones = {}
    self.bone_transforms = [np.eye(4, dtype=float) for _ in xrange(60)]
    self.action_controller = None
    self.will_animate = will_animate
    self.position = np.array(position, dtype=np.float32)
    self.last_unanimated_position = position
    if self.will_animate:
      self.offset = np.zeros(3)
    else:
      self.offset = np.array(offset, dtype=np.float32)
    self.direction = np.array((0, 0, 1), dtype=float)
    self.bidirection = np.array((1, 0, 0), dtype=float)
    self.angle = angle
    self.daemon = daemon

    self.shader                = Shaders.getShader("general-noninstanced")
    self.shader["colormap"]    = Texture.COLORMAP_NUM
    self.shader["normalmap"]   = Texture.NORMALMAP_NUM
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
    logging.info("Loading object {} from {}".format(self.name, self.filename))
    full_meshes = []

    def get_mesh_info():
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
      logging.info("Postprocessing {}".format(self.name))

      mesh_info = []

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
      return mesh_info

    self.bones = dent.assets.getAsset(self.name + "-bones", lambda: {})

    mesh_info = dent.assets.getAsset(self.name + "-mesh_info", get_mesh_info)
    if full_meshes:
      mesh_info = full_meshes
    for mesh in mesh_info:
      self.addMesh(*mesh)

    self.bones = dent.assets.getAsset(
        self.name + "-bones", lambda: self.bones, forceReload=True
    )

  def addMesh(self, name, assimp_mesh, trans):
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

    mesh.load_textures()
    if mesh.normal_texture_file:
        options = options._replace(has_bumpmap=True)
    else:
        options = options._replace(has_bumpmap=False)

    # Do skinning
    if self.will_animate:
      if len(self.bones) > 0:
        options = options._replace(has_bones=True)

    self.meshes.append(MeshDatum(name, mesh.data, mesh.indices, options, mesh))

    taskQueue.addToMainThreadQueue(self.uploadMesh, (mesh.data, mesh.indices, mesh))

  def uploadMesh(self, data, indices, mesh):
    self.renderIDs.append(self.shader.setData(data, indices))
    logging.info("Loaded mesh {}".format(mesh.__repr__()))

  def update(self, time=0):
    if self.action_controller is not None:
      self.action_controller.update(time)

  def display(self):
    self.shader.load()
    t = np.eye(4, dtype=np.float32)
    t[2, 0:3] = self.direction
    t[0, 0:3] = self.bidirection
    t[0][0:3], t[2][0:3] = np.cos(self.angle) * t[0][0:3] + np.sin(self.angle) * t[2][0:3],\
                           np.cos(self.angle) * t[2][0:3] - np.sin(self.angle) * t[0][0:3]
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

    options = None
    if self.action_controller is not None:
      self.shader["bones"] = self.bone_transforms
    for meshdatum, renderID in zip(self.meshes, self.renderIDs):
      # Set options
      if options != getOptionNumber(meshdatum.options):
        options = getOptionNumber(meshdatum.options)
        self.shader["options"] = options

      # Load textures
      meshdatum.mesh.set_material_uniforms(self.shader)
      self.shader.draw(gl.GL_TRIANGLES, renderID)

  def add_animation(self, filename):
    if self.action_controller is None:
      self.action_controller = ActionController.ActionController(self)

    animation = Animation.Animation(filename, self.bones)
    self.action_controller.add_action(animation)

    self.last_unanimated_position = self.position

  def __repr__(self):
    return '<pmObject "{}">'.format(self.name)
