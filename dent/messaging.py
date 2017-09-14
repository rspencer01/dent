import time
import cPickle as pickle
from collections import deque
import copy
import gzip

time_zero = 0
handled_messages = []
messages = deque()
handlers = {}
replaying = False

class Message(object):
  def __init__(self, message_type, data=()):
    self.time = time.time() - time_zero
    self.type = message_type
    self.data = data

  def __repr__(self):
    return "{0.time:.2f} {0.type} {0.data}".format(self)

def add_message(message):
  """Adds a new message to the queue."""
  if replaying:
    return
  messages.append(message)

def add_handler(message_type, handler):
  if message_type not in handlers:
    handlers[message_type] = []
  handlers[message_type].append(handler)

def process_messages():
  global messages, handled_messages
  game_time = time.time() - time_zero
  while len(messages):
    message = messages.popleft()
    if game_time >= message.time:
      handled_messages.append(message)
      if message.type in handlers:
        for handler in handlers[message.type]:
          handler(*message.data)
    else:
      messages.appendleft(message)
      break

def game_start_handler(time):
  global handled_messages
  global time_zero
  assert len(handled_messages) == 1
  assert handled_messages[0].type == 'game_start'
  handled_messages[0].time = 0
  time_zero = time
  for message in messages:
    message.time -= time_zero

add_handler('game_start', game_start_handler)

def save_messages(filename='replay.log'):
  """Saves all processed and unprocessed messages to a file."""
  all_messages = copy.copy(messages)
  all_messages.extendleft(handled_messages[::-1])
  pickle.dump(all_messages, gzip.open(filename, 'wb'))

def load_messages(filename='replay.log'):
  """Loads all messages in a given file."""
  return pickle.load(gzip.open(filename, 'rb'))

def load_replay(filename='replay.log'):
  """Must be called when the only item on the message queue is `begin_game`.
  Loads the message queue from the given file."""
  global messages, handled_messages, replaying
  assert len(messages) == 1
  assert len(handled_messages) == 0
  process_messages()
  handled_messages = []
  messages = load_messages(filename)
  messages.popleft()
  replaying = True

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description='Magrathea messaging service inspector.')
  parser.add_argument('log', 
      default='replay.log', 
      nargs='?',
      help='log file to inspect')
  args = parser.parse_args()

  for message in load_messages(args.log):
    print message
