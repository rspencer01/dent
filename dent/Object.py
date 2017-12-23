import OpenGL.GL as gl
import os
import numpy as np
import pyassimp
import pyassimp.material
import Texture
import TextureManager
import Shaders
import transforms
import logging
import taskQueue
import threading
import ActionController
from collections import namedtuple
import Animation

MeshOptions = namedtuple("MeshOptions", ('has_bumpmap', 'has_bones'))
MeshDatum = namedtuple("MeshDatum", ('name', 'data', 'indices', 'colormap', 'normalmap', 'specularmap', 'options'))

def getOptionNumber(meshOptions):
  ans = 0
  for i,v in enumerate(meshOptions):
    if v:
      ans += 2 ** i
  return ans

def get_node_parent(scene, name):
  def dfs(node,parent):
    if node.name == name:
      return parent
    for i in node.children:
      a = dfs(i, node)
      if a: return a
    return None
  return dfs(scene.rootnode, '')

def getTextureFile(material, textureType, directory=None):
  if textureType == pyassimp.material.aiTextureType_DIFFUSE:
    if os.path.exists(directory+'/{}.diff.png'.format(material.properties[('name', 0)])):
      return '{}.diff.png'.format(material.properties[('name', 0)])
  elif textureType == pyassimp.material.aiTextureType_NORMALS:
    if os.path.exists(directory+'/{}.norm.png'.format(material.properties[('name', 0)])):
      return '{}.norm.png'.format(material.properties[('name', 0)])
  elif textureType == pyassimp.material.aiTextureType_SPECULAR:
    if os.path.exists(directory+'/{}.spec.png'.format(material.properties[('name', 0)])):
      return '{}.spec.png'.format(material.properties[('name', 0)])
  if ('file', textureType) in material.properties:
    if os.path.exists(directory+'/{}'.format(material.properties[('file', textureType)])):
      return material.properties[('file', textureType)]
  logging.debug("Texture {}/{} not found".format(directory,material.properties[('name', 0)]))

shader             = Shaders.getShader('general-noninstanced')
shader['colormap'] = Texture.COLORMAP_NUM
shader['normalmap'] = Texture.NORMALMAP_NUM
shader['specularmap'] = Texture.SPECULARMAP_NUM

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
      daemon=True):

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
    self.textures = []
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
    self.direction = np.array((0,0,1), dtype=float)
    self.bidirection = np.array((1,0,0), dtype=float)
    self.angle = angle
    self.daemon = daemon

    self.bounding_box_min = np.zeros(3, dtype=float) + 1e10
    self.bounding_box_max = np.zeros(3, dtype=float) - 1e10

    if self.filename[-4:] == '.fbx':
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
    # Some of these are for static only and must be removed when doing bones.
    self.scene = pyassimp.load(self.filename,
        processing=pyassimp.postprocess.aiProcess_CalcTangentSpace|
                   pyassimp.postprocess.aiProcess_Triangulate|
                   pyassimp.postprocess.aiProcess_JoinIdenticalVertices|
                   pyassimp.postprocess.aiProcess_LimitBoneWeights |
                   pyassimp.postprocess.aiProcess_GenNormals)

    def addNode(node, trans, depth = 0):
      newtrans = trans.dot(node.transformation)
      for msh in node.meshes:
        self.addMesh(node.name, msh, newtrans)
      for nod in node.children:
        addNode(nod, newtrans, depth+1)

    t = np.eye(4)
    addNode(self.scene.rootnode, t)


  def addMesh(self, name, mesh, trans):
    logging.debug("Loading mesh {}".format(mesh.__repr__()))
    options = MeshOptions(False, False)
    data = np.zeros(len(mesh.vertices),
                      dtype=[("position" , np.float32,3),
                             ("normal"   , np.float32,3),
                             ("textcoord", np.float32,2),
                             ("tangent"  , np.float32,3),
                             ("bitangent", np.float32,3),
                             ("bone_ids", np.int32,4),
                             ("weights", np.float32,4)])
    # Get the vertex positions and add a w=1 component
    vertPos = mesh.vertices
    add = np.ones((vertPos.shape[0], 1),dtype=np.float32)
    vertPos = np.append(vertPos, add, axis=1)
    # Get the vertex normals and add a w=1 component
    vertNorm = mesh.normals
    add = np.zeros((vertNorm.shape[0],1),dtype=np.float32)
    vertNorm = np.append(vertNorm, add, axis=1)

    vertTangents = mesh.tangents
    vertBitangents = mesh.bitangents

    tinvtrans = np.linalg.inv(trans).transpose()
    # Transform all the vertex positions.
    for i in xrange(len(vertPos)):
      vertPos[i] = trans.dot(vertPos[i])
      vertNorm[i] = tinvtrans.dot(vertNorm[i])
    # Splice correctly, killing last components
    vertPos = vertPos[:,0:3] - self.offset
    vertNorm = vertNorm[:,0:3]

    vertUV = mesh.texturecoords[0][:, [0,1]]
    vertUV[:, 1] = 1 - vertUV[:, 1]

    # Update the bounding box
    self.bounding_box_min = np.min([self.bounding_box_min,
                                    np.min(vertPos, 0)],0)
    self.bounding_box_max = np.max([self.bounding_box_min,
                                    np.max(vertPos, 0)],0)

    # Set the data
    data["position"] = vertPos
    data["normal"] = vertNorm
    data["textcoord"] = vertUV
    data["tangent"] = vertTangents
    data["bone_ids"] = 59
    data["bitangent"] = vertBitangents

    # Get the indices
    indices = mesh.faces.reshape((-1,))

    # Load the texture
    if getTextureFile(mesh.material, pyassimp.material.aiTextureType_DIFFUSE, self.directory):
      texture = TextureManager.get_texture(self.directory+'/'+getTextureFile(mesh.material, pyassimp.material.aiTextureType_DIFFUSE, self.directory), Texture.COLORMAP)
    else:
      texture = Texture.getWhiteTexture();

    if getTextureFile(mesh.material, pyassimp.material.aiTextureType_NORMALS, self.directory):
      normalTexture = TextureManager.get_texture(self.directory+'/'+getTextureFile(mesh.material, pyassimp.material.aiTextureType_NORMALS, self.directory), Texture.NORMALMAP)
      options = options._replace(has_bumpmap=True)
    elif getTextureFile(mesh.material, pyassimp.material.aiTextureType_HEIGHT, self.directory):
      normalTexture = TextureManager.get_texture(self.directory+'/'+getTextureFile(mesh.material, pyassimp.material.aiTextureType_HEIGHT, self.directory), Texture.NORMALMAP)
      options = options._replace(has_bumpmap=True)
    else:
      normalTexture = None
      options = options._replace(has_bumpmap=False)

    if getTextureFile(mesh.material, pyassimp.material.aiTextureType_SPECULAR, self.directory):
      logging.info("Getting texture from {}".format(getTextureFile(mesh.material, pyassimp.material.aiTextureType_SPECULAR, self.directory)))
      specTexture = TextureManager.get_texture(self.directory+'/'+getTextureFile(mesh.material, pyassimp.material.aiTextureType_SPECULAR, self.directory), Texture.SPECULARMAP)
    else:
      specTexture = Texture.getBlackTexture()
      specTexture.textureType = Texture.SPECULARMAP

    # Do skinning
    if self.will_animate:
      if len(mesh.bones) > 0:
        options = options._replace(has_bones=True)
        data["weights"] = 0
        for bone in mesh.bones:
          n = len(self.bones)
          if bone.name not in self.bones:
            self.bones[bone.name] = (n, get_node_parent(self.scene, bone.name).name, bone.offsetmatrix)
            nn =n
          else:
            nn = self.bones[bone.name][0]
          for relationship in bone.weights:
            bone_vec_number = 0
            for i in xrange(3):
              if data["weights"][relationship.vertexid][bone_vec_number] > 0:
                bone_vec_number += 1
              else:
                break
            data["weights"][relationship.vertexid][bone_vec_number] = relationship.weight
            data["bone_ids"][relationship.vertexid][bone_vec_number] = nn
    # Add the textures and the mesh data
    self.textures.append(texture)
    self.meshes.append(MeshDatum(name, data, indices, texture, normalTexture, specTexture, options))

    taskQueue.addToMainThreadQueue(self.uploadMesh, (data, indices, mesh))


  def uploadMesh(self, data, indices, mesh):
    self.renderIDs.append(shader.setData(data, indices))
    logging.info("Loaded mesh {}".format(mesh.__repr__()))


  def update(self, time=0):
    if self.action_controller is not None:
      self.action_controller.update(time)


  def display(self):
    shader.load()
    t = np.eye(4, dtype=np.float32)
    t[2,0:3] = self.direction
    t[0,0:3] = self.bidirection
    t[0][0:3], t[2][0:3] = np.cos(self.angle) * t[0][0:3] + np.sin(self.angle) * t[2][0:3],\
                           np.cos(self.angle) * t[2][0:3] - np.sin(self.angle) * t[0][0:3]
    t[0:3,0:3] *= self.scale
    transforms.translate(t, self.last_unanimated_position[0], self.last_unanimated_position[1], self.last_unanimated_position[2])
    shader['model'] = t

    options = None
    if self.action_controller is not None:
      shader['bones'] = self.bone_transforms

    for meshdatum,renderID in zip(self.meshes,self.renderIDs):
      # Set options
      if options != getOptionNumber(meshdatum.options):
        options = getOptionNumber(meshdatum.options)
        shader['options'] = options

      # Load textures
      meshdatum.colormap.load()
      meshdatum.specularmap.load()
      if meshdatum.options.has_bumpmap:
        meshdatum.normalmap.load()
      shader.draw(gl.GL_TRIANGLES, renderID)


  def add_animation(self, filename):
    if self.action_controller is None:
      self.action_controller = ActionController.ActionController(self)

    animation = Animation.Animation(filename, self.bones)
    self.action_controller.add_action(animation)

    self.last_unanimated_position = self.position


  def __repr__(self):
    return "<pmObject \"{}\">".format(self.name)
