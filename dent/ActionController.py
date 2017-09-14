import yaml
import random
from Animation import Animation

class ActionController(object):
  """Controls the action (movement etc) of an asset."""

  def __init__(self, owner, configuration_file=None, follow_animation=True):
    self.actions = []
    self.current_action_id = 0
    self.owner = owner
    self.last_action_changeover = 0
    self.chaining = False
    if configuration_file:
      self._configuration = yaml.load(open(configuration_file).read())
      for i in self._configuration['actions']:
        animation = Animation(i['file'], owner.bones, looping=False)
        self.actions.append(animation)
      self.chaining = self._configuration['chaining']
      self.owner.follow_animation = follow_animation
    self.action_weight = lambda x: 1


  def add_action(self, action):
    self.actions.append(action)


  def current_animation(self):
    assert self.current_action_id < len(self.actions)
    return self.actions[self.current_action_id]


  def update(self, time):
    time_into_action = time - self.last_action_changeover
    if self.current_animation().get_state(time_into_action) == 'finished':
      self.last_action_changeover = time

      self.owner.last_unanimated_position = self.owner.position -\
                      self.current_animation().get_root_offset(time_into_action) * self.owner.scale

      weights = [(-self.action_weight(self.actions[i]),i) for i in xrange(len(self.actions))]
      random.shuffle(weights)
      weights.sort(key=lambda x: x[0])
      self.current_action_id = weights[0][1]
    else:
      self.owner.bone_transforms = self.current_animation() \
                                       .get_bone_transforms(time_into_action, not self.chaining)
      if self.chaining:
        self.owner.position = self.owner.last_unanimated_position +\
                          self.current_animation().get_root_offset(time_into_action) * self.owner.scale
