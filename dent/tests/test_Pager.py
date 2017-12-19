from dent.Pager import Pager

def test_virgin_size():
  assert len(Pager(4)) == 0

def test_virgin_empty():
  p = Pager(4)
  for i in range(4):
    assert i not in p

def test_oldest_removed():
  p = Pager(3)
  for i in range(4):
    p.add(i)
  assert 0 not in p
  for i in range(1,4):
    assert i in p

def test_touching():
  p = Pager(3)
  for i in range(4):
    p.add(i)
    a = p[0]
  assert 0 in p

def test_adding_and_removing():
  p = Pager(3)
  p.add('first')
  assert len(p) == 1
  p.add('second')
  assert len(p) == 2
  p.remove('first')
  assert len(p) == 1

def test_clear():
  p = Pager(3)
  for i in range(3):
    p.add(i)
  assert len(p) > 0
  p.clear()
  assert len(p) == 0
