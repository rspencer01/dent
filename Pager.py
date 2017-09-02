import time
import random
random.seed(0)

class Pager(object):
  def __init__(self, size):
    self.mapping = {}
    self.available_indices = set(range(size))


  def remove_oldest(self):
    oldest = sorted(self.mapping.items(),key = lambda x: x[1][0])[0][0]
    self.remove(oldest)


  def remove(self, item):
    if item not in self: return
    self.available_indices.add(self.mapping[item][1])
    del self.mapping[item]


  def add(self, item):
    if len(self.available_indices) == 0:
      self.remove_oldest()
    index = random.choice(list(self.available_indices))
    self.available_indices.remove(index)
    self.mapping[item] = (time.time(), index)
    return index


  def clear(self):
    while len(self):
      self.remove_oldest()


  def minimise_indices(self):
    """After calling, all the items are guaranteed to be in positions 0 to
    (n-1), where there are n indices.  Returns a mapping from old indices to new
    ones. Not guaranteed to use the fewest movements at all."""
    transfer = {}
    keys = self.mapping.keys
    newmapping = {}
    for n,i in keys:
      transfer[i] = n
      newmapping[n] = i
    self.mapping = newmapping


  def __getitem__(self, item):
    v = self.mapping[item][1]
    self.mapping[item] = (time.time(),v)
    return v


  def __contains__(self, item):
    return item in self.mapping


  def __len__(self):
    return len(self.mapping)
