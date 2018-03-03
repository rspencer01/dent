import dent.messaging

keys_down = set()

def keyboard_up_handler(key):
  if key in keys_down:
    keys_down.remove(key)


def keyboard_handler(key):
  keys_down.add(key)


def is_key_down(key):
  """Checks if the given key is currently pressed.

  This function should be used by the game as a central way to check the state
  of the keyboard for things like character motion etc that rely on continuous
  key press.

  Events that occur on the event of a key being is pressed should be handled
  with a message handler."""
  return key in keys_down

dent.messaging.add_handler('keyboard', keyboard_handler)
dent.messaging.add_handler('keyboard_up', keyboard_up_handler)
