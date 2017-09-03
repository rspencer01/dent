import numpy as np
import pyassimp
import transforms
from collections import namedtuple
import yaml

Bone = namedtuple("Bone", ('name', 'parent_name', 'id', 'children', 'offsetmatrix'))

def get_children(bones, bone):
  return [i.name for i in bones if i.parent_name == bone.name]

def basic_animation(filename):
  return {
      'animation_filename': filename,
      'animation_index': 0,
      'looping': True,
      }

class Animation(object):
  def __init__(self, filename, bones):
    if filename[-5:] == '.yaml':
      self._configuration = yaml.load(open(filename).read())
    else:
      self._configuration = basic_animation(filename)
    self._animation = pyassimp.load(self._configuration['animation_filename']).animations[self._configuration['animation_index']]
    if 'animation_fps' not in self._configuration:
      self._configuration['animation_fps'] = self._animation.tickspersecond
    if 'animation_frames' not in self._configuration:
      self._configuration['animation_frames'] = int(self._animation.duration)

    self._bones = [Bone(i, j[1], j[0],[],j[2]) for i,j in bones.items()]
    self._bones = [Bone(i.name, i.parent_name, i.id, get_children(self._bones, i), i.offsetmatrix) for i in self._bones]

  def get_bone_transforms(self, time, with_root_offset=True):
    time = int(time * self._configuration['animation_fps']) \
            % (self._configuration['animation_frames'])

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
    time = int(time * self._configuration['animation_fps']) \
            % (self._configuration['animation_frames'])

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


  def get_state(self, time):
    if not self._configuration['looping']:
      time = int(time * self._configuration['animation_fps'])
      if time > self._configuration['animation_frames'] - 1:
        return 'finished'
    return 'running'
