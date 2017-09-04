import yaml
from Animation import Animation

class ActionController(object):
  """Controls the action (movement etc) of an asset."""

  def __init__(self, owner, configuration_file=None):
    self.actions = []
    self.current_action_id = 0
    self.owner = owner
    if configuration_file:
      self._configuration = yaml.load(open(configuration_file).read())
      for i in self._configuration['actions']:
        animation = Animation(i['file'], owner.bones)
        self.actions.append(animation)
      self.owner.follow_animation = True



  def add_action(self, action):
    self.actions.append(action)


  def current_animation(self):
    assert self.current_action_id < len(self.actions)
    return self.actions[self.current_action_id]


  def update(self, time):
    self.owner.bone_transforms = self.current_animation().get_bone_transforms(time, False)
    self.owner.position = self.owner.last_unanimated_position +\
                      self.current_animation().get_root_offset(time) * self.owner.scale
