import time

class Pager(dict):
  def __init__(self, size):
    self.available_indices = set(range(size))


  def _remove_oldest(self):
    oldest = sorted(list(self.items()), key = lambda x: x[1][0])[0][0]
    self.remove(oldest)


  def remove(self, item):
    assert item in self
    self.available_indices.add(self[item])
    del self[item]


  def add(self, item):
    if len(self.available_indices) == 0:
      self._remove_oldest()
    index = self.available_indices.pop()
    self[item] = (time.time(), index)
    return index


  def __getitem__(self, item):
    assert item in self
    v = super(Pager,self).__getitem__(item)[1]
    self[item] = (time.time(),v)
    return v
