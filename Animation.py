import numpy as np
import pyassimp
import transforms
from collections import namedtuple

Bone = namedtuple("Bone", ('name', 'parent_name', 'id', 'children', 'offsetmatrix'))

def get_children(bones, bone):
  return [i.name for i in bones if i.parent_name == bone.name]

class Animation(object):
  def __init__(self, filename, bones):
    self._animation = pyassimp.load(filename, pyassimp.postprocess.aiProcess_MakeLeftHanded).animations[0]
    self._bones = [Bone(i, j[1], j[0],[],j[2]) for i,j in bones.items()]
    self._bones = [Bone(i.name, i.parent_name, i.id, get_children(self._bones, i), i.offsetmatrix) for i in self._bones]

  def get_bone_transforms(self, time, with_root_offset=True):
    time = int(time)
    bones = np.zeros((60,4,4), dtype=np.float32)
    for i in xrange(60):
      bones[i] = np.eye(4)
      bones[i,:3,:3]*=0

    def dfs(name, t, lastvalidoffset=None, nooffset=False):
      transform = self.get_channel(name)
      bone = self.get_bone(name)
      if transform:
        position = transform.positionkeys[time % len(transform.positionkeys)].value
        rotation = transform.rotationkeys[time % len(transform.rotationkeys)].value
        if not nooffset:
          t = transforms.translate2(*position).dot(t)
        t = transforms.quaternion_matrix(rotation).T.dot(t)
        bones[bone.id] = bone.offsetmatrix.T.dot(t)
        lastvalidoffset = bone.offsetmatrix.T
      else:
        bones[bone.id] = lastvalidoffset.dot(t)
      for i in self.get_bone(name).children:
        dfs(i, t[:,:],lastvalidoffset)
    dfs('Hips', np.eye(4, dtype=np.float32), nooffset=not with_root_offset)
    return bones


  def get_root_offset(self, time):
    time = int(time)

    positionkeys = self.get_channel('Hips').positionkeys
    return positionkeys[time % len(positionkeys)].value


  def has_bone(self, n):
    return n.upper() in [i.name.upper() for i in self._bones]


  def get_bone(self, name):
    for i in self._bones:
      if i.name.upper() == name.upper():
        return i


  def get_channel(self, channelname):
    for i in self._animation.channels:
      if i.nodename.data.upper() == channelname.upper():
        return i
    return None

