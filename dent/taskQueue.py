import time
from collections import namedtuple, deque

Task = namedtuple('Task', ('func', 'args', 'priority'))

mainThreadQueue = deque()
lastMainThread = 0

def addToMainThreadQueue(func, args=(), priority=1):
  mainThreadQueue.append(Task(func, args, priority))

def doNextTask():
  global mainThreadQueue, lastMainThread
  if len(mainThreadQueue) == 0:
    return

  if time.time() - lastMainThread > 0.2 / mainThreadQueue[0].priority:
    item = mainThreadQueue.popleft()
    item.func(*item.args)
    lastMainThread = time.time()

