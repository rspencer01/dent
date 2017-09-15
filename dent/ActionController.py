import random
from Animation import Animation
import numpy as np

class ActionController(object):
  """Controls the action (movement and animation) of an asset."""

  def __init__(self, owner):
    self.actions = []
    self._current_action_id = 0
    self.owner = owner
    self.last_action_changeover = 0
    self.chaining = True
    self.action_weight = lambda x: 1


  def add_action(self, action):
    self.actions.append(action)


  def current_animation(self):
    assert self._current_action_id < len(self.actions)
    return self.actions[self._current_action_id]


  def update(self, time):
    """Updates the state of the object's actions.  When called, this function
    will update the parent object's bone structure.  It may also change the
    current action that the object is performing."""
    time_into_action = time - self.last_action_changeover
    if self.current_animation().get_state(time_into_action) == 'finished':
      self.last_action_changeover = time

      self.owner.last_unanimated_position = self.owner.position
      self.owner.angle += self.current_animation().get_end_rotation()

      weights = [(-self.action_weight(self.actions[i]),i) for i in xrange(len(self.actions))]
      random.shuffle(weights)
      weights.sort(key=lambda x: x[0])
      self._current_action_id = weights[0][1]

    time_into_action = time - self.last_action_changeover
    self.owner.bone_transforms = self.current_animation() \
                                     .get_bone_transforms(time_into_action, True)
    diff = (self.current_animation().get_root_offset(time_into_action) - self.current_animation().get_root_offset(0)) * self.owner.scale
    r = self.owner.angle
    diff[0], diff[2] = np.cos(r) * diff[0] - np.sin(r) * diff[2],\
                       np.cos(r) * diff[2] + np.sin(r) * diff[0]
    self.owner.position = self.owner.last_unanimated_position + diff
