class ActionController(object):
  """Controls the action (movement etc) of an asset."""

  def __init__(self, owner):
    self.actions = []
    self.current_action_id = 0
    self.owner = owner


  def add_action(self, action):
    self.actions.append(action)


  def current_animation(self):
    assert self.current_action_id < len(self.actions)
    return self.actions[self.current_action_id]


  def update(self, time):
    self.owner.bone_transforms = self.current_animation().get_bone_transforms(time, not self.owner.follow_animation)
    self.owner.position = self.owner.last_unanimated_position +\
                      self.current_animation().get_root_offset(time) * self.owner.scale