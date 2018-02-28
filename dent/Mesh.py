import numpy as np
import logging
import pyassimp.material
import os

def getTextureFile(material, textureType, directory=None):
  """Finds the filepath of a texture given the material."""
  dent_formats = {pyassimp.material.aiTextureType_DIFFUSE: "{}.diff.png",
                  pyassimp.material.aiTextureType_NORMALS: "{}.norm.png",
                  pyassimp.material.aiTextureType_SPECULAR: "{}.spec.png"}
  if textureType in dent_formats:
    filename = os.path.join(
        directory,
        dent_formats[textureType].format(material.properties[('name', 0)]))
    if os.path.exists(filename):
      return dent_formats[textureType].format(material.properties[('name', 0)])
  elif ('file', textureType) in material.properties:
    filename = os.path.join(
        directory,
        material.properties[('file', textureType)])
    if os.path.exists(filename):
      return material.properties[('file', textureType)]
  logging.debug("Texture {}/{} not found".format(directory,material.properties[('name', 0)]))

def get_node_parent(scene, name):
  def dfs(node,parent):
    if node.name == name:
      return parent
    for i in node.children:
      a = dfs(i, node)
      if a: return a
    return None
  return dfs(scene.rootnode, '')


class Mesh(object):
  def __init__(self, name, transform, offset):
    self.name = name
    self.data = None
    self.indices = None
    self.transform = transform
    self.offset = offset
    self.diffuse_texture_file = None
    self.normal_texture_file = None
    self.specular_texture_file = None


  def load_from_assimp(self, assimp_mesh, directory, scene, parent):
    self.data = np.zeros(len(assimp_mesh.vertices),
                         dtype=[("position" , np.float32,3),
                                ("normal"   , np.float32,3),
                                ("textcoord", np.float32,2),
                                ("tangent"  , np.float32,3),
                                ("bitangent", np.float32,3),
                                ("bone_ids", np.int32,4),
                                ("weights", np.float32,4)])

    # Get the vertex positions and add a w=1 component
    vertPos = assimp_mesh.vertices
    add = np.ones((vertPos.shape[0], 1),dtype=np.float32)
    vertPos = np.append(vertPos, add, axis=1)
    # Get the vertex normals and add a w=1 component
    vertNorm = assimp_mesh.normals
    add = np.zeros((vertNorm.shape[0],1),dtype=np.float32)
    vertNorm = np.append(vertNorm, add, axis=1)

    vertTangents = assimp_mesh.tangents
    vertBitangents = assimp_mesh.bitangents

    tinvtrans = np.linalg.inv(self.transform).transpose()
    # Transform all the vertex positions.
    for i in xrange(len(vertPos)):
      vertPos[i] = self.transform.dot(vertPos[i])
      vertNorm[i] = tinvtrans.dot(vertNorm[i])
    # Splice correctly, killing last components
    vertPos = vertPos[:,0:3] - self.offset
    vertNorm = vertNorm[:,0:3]

    vertUV = assimp_mesh.texturecoords[0][:, [0,1]]
    vertUV[:, 1] = 1 - vertUV[:, 1]

    # Set the data
    self.data["position"] = vertPos
    self.data["normal"] = vertNorm
    self.data["textcoord"] = vertUV
    self.data["tangent"] = vertTangents
    self.data["bone_ids"] = 59
    self.data["bitangent"] = vertBitangents
    self.data["weights"] = 0

    # Get the indices
    self.indices = assimp_mesh.faces.reshape((-1,))

    # Load the texture
    self.diffuse_texture_file = getTextureFile(assimp_mesh.material, pyassimp.material.aiTextureType_DIFFUSE, directory)
    self.normal_texture_file = getTextureFile(assimp_mesh.material, pyassimp.material.aiTextureType_NORMALS, directory) or \
                               getTextureFile(assimp_mesh.material, pyassimp.material.aiTextureType_HEIGHT, directory)
    self.specular_texture_file = getTextureFile(assimp_mesh.material, pyassimp.material.aiTextureType_SPECULAR, directory)

    if len(assimp_mesh.bones) > 0:
      for bone in assimp_mesh.bones:
        n = len(parent.bones)
        if bone.name not in parent.bones:
          parent.bones[bone.name] = (n, get_node_parent(scene, bone.name).name, bone.offsetmatrix)
          nn =n
        else:
          nn = parent.bones[bone.name][0]
        for relationship in bone.weights:
          bone_vec_number = 0
          for i in xrange(3):
            if self.data["weights"][relationship.vertexid][bone_vec_number] > 0:
              bone_vec_number += 1
            else:
              break
          self.data["weights"][relationship.vertexid][bone_vec_number] = relationship.weight
          self.data["bone_ids"][relationship.vertexid][bone_vec_number] = nn
