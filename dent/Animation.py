import numpy as np
import StringIO
import tarfile
import pyassimp
import transforms
from collections import namedtuple
import yaml
import cPickle as pickle

Bone = namedtuple("Bone", ('name', 'parent_name', 'id', 'children', 'offsetmatrix', 'positions','rotations'))

def get_children(bones, bone):
  return [i.name for i in bones if i.parent_name == bone.name]

def basic_animation(filename):
  return {
      'animation_filename': filename,
      'animation_index': 0,
      'looping': True,
      }

class Animation(object):
  def __init__(self):
    self.cached_bone_values = {}

  def load_from_file(self,filename,bones):
    if filename[-5:] == '.yaml':
      self._configuration = yaml.load(open(filename).read())
    else:
      self._configuration = basic_animation(filename)

    if 'animation_filename' in self._configuration:
      self._animation = pyassimp.load(self._configuration['animation_filename']).animations[self._configuration['animation_index']]
    else:
      self._animation = False
    if 'invert' not in self._configuration:
      self._configuration['invert'] = False
    if 'animation_fps' not in self._configuration:
      self._configuration['animation_fps'] = self._animation.tickspersecond
    if 'animation_frames' not in self._configuration:
      self._configuration['animation_frames'] = int(self._animation.duration)
    if 'end_position' not in self._configuration:
      self._configuration['end_position'] = [0,0,0]
    if 'end_rotation' not in self._configuration:
      self._configuration['end_rotation'] = 0
    self._configuration['looping'] = self._configuration['looping']

    self._bones = [Bone(i, j[1], j[0],[],j[2], None, None) for i,j in bones.items()]
    self._bones = [Bone(i.name, i.parent_name, i.id, get_children(self._bones, i), i.offsetmatrix, None,None) for i in self._bones]

    self.read_from_assimp(self._animation)

  def read_from_assimp(self, assimp_animation):
    for i in xrange(len(self._bones)):
      channel = self.get_channel(self._bones[i].name)
      if not channel:
        positionkeys = np.zeros((int(self._animation.duration), 3))
        rotationkeys = np.zeros((int(self._animation.duration), 3))
      else:
        positionkeys = np.array([j.value for j in channel.positionkeys])
        rotationkeys = np.array([j.value for j in channel.rotationkeys])
      self._bones[i] = self._bones[i]._replace(positions=positionkeys)
      self._bones[i] = self._bones[i]._replace(rotations=rotationkeys)

  def get_bone_transforms(self, time, with_root_offset=True):
    time = int(time * self._configuration['animation_fps']) \
            % (self._configuration['animation_frames'])
    if self._configuration['invert']:
      time = self._configuration['animation_frames'] - time - 1

    if time not in self.cached_bone_values:
      bones = np.zeros((60,4,4), dtype=np.float32)
      for i in xrange(60):
        bones[i] = np.eye(4)
        bones[i,:3,:3]*=0

      def dfs(name, t, lastvalidoffset=None, nooffset=False):
        bone = self.get_bone(name)
        if bone:
          position = bone.positions[time % len(bone.positions)]
          rotation = bone.rotations[time % len(bone.rotations)]
          if not nooffset:
            t = transforms.translate2(*position).dot(t)
          t = transforms.quaternion_matrix(rotation).T.dot(t)
          bones[bone.id] = bone.offsetmatrix.T.dot(t)
          lastvalidoffset = bone.offsetmatrix.T
        else:
          bones[bone.id] = lastvalidoffset.dot(t)
        for i in self.get_bone(name).children:
          dfs(i, t[:,:],lastvalidoffset)
      if self._bones:
        dfs('Hips', np.eye(4, dtype=np.float32), nooffset=not with_root_offset)
      else:
        for i in xrange(60):
          bones[i] = np.eye(4)
          bones[i][0][0] = np.cos(self._configuration['end_rotation'] * float(time) / self._configuration['animation_frames'])
          bones[i][2][2] = np.cos(self._configuration['end_rotation'] * float(time) / self._configuration['animation_frames'])
          bones[i][2][0] = -np.sin(self._configuration['end_rotation'] * float(time) / self._configuration['animation_frames'])
          bones[i][0][2] = np.sin(self._configuration['end_rotation'] * float(time) / self._configuration['animation_frames'])
          if with_root_offset:
            bones[i][3,0:3] = np.array(self._configuration['end_position']) * float(time) / self._configuration['animation_frames']

      self.cached_bone_values[time] = bones
    return self.cached_bone_values[time]


  def get_root_offset(self, time):
    time = int(time * self._configuration['animation_fps']) \
            % (self._configuration['animation_frames'])
    if self._configuration['invert']:
      time = self._configuration['animation_frames'] - time - 1

    if self._bones:
      positionkeys = self.get_bone('Hips').positions
      return positionkeys[time % len(positionkeys)]
    else:
      return np.array(self._configuration['end_position']) * time / float(self._configuration['animation_frames'])


  def get_end_position(self):
    """Returns the position of the animation in the last frame."""
    if self._bones:
      positionkeys = self.get_bone('Hips').positions
      if self._configuration['invert']:
        return -positionkeys[0]
      return positionkeys[-1]
    else:
      return np.array(self._configuration['end_position'])


  def get_end_rotation(self):
    """Returns the rotation of the animation in the last frame."""
    if self.bones:
      return 0
    else:
      return self._configuration['end_rotation']


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

  @staticmethod
  def _dent_asset_load(datastore):
      if "data" not in datastore.getnames():
          raise IOError()

      animation = Animation()
      data = pickle.load(datastore.extractfile("data"))
      animation._configuration = data['configuration']
      animation._bones = data['bones']
      return animation

  def _dent_asset_save(self, datastore):
      """Saves the image in this texture to a dent asset datastore."""
      data_buffer = StringIO.StringIO()
      pickle.dump({
        'configuration':self._configuration,
        'bones':self._bones,
        },data_buffer)
      data_buffer.flush()
      data_buffer.seek(0)
      data_header = tarfile.TarInfo("data")
      data_header.size = data_buffer.len
      datastore.addfile(data_header, data_buffer)
