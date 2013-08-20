import collections


MAX_EDICT_BITS = 11


def to_ehandle(index, serial):
  return (serial << MAX_EDICT_BITS) | index


def from_ehandle(ehandle):
  index = ehandle & ((1 << MAX_EDICT_BITS) - 1)
  serial = ehandle >> MAX_EDICT_BITS
  return index, serial


def construct(*args):
  return World(*args)


class World(object):
  def __init__(self, recv_tables, entities=None):
    entities = entities or []
    self.recv_tables = recv_tables

    self.by_index = collections.OrderedDict()
    self.by_ehandle = collections.OrderedDict()
    self.by_cls = collections.defaultdict(list)
    self.by_dt = collections.defaultdict(list)
    self.classes = {}

  def __iter__(self):
    return iter(self.by_ehandle.items())

  def create(self, cls, index, serial, state):
    dt = self.recv_tables[cls].dt
    ehandle = to_ehandle(index, serial)

    # no assertions because of duplicate creation at replay start
    self.by_index[index] = ehandle
    self.by_ehandle[ehandle] = state
    self.by_cls[cls].append(ehandle)
    self.by_dt[dt].append(ehandle)
    self.classes[ehandle] = cls

  def update(self, index, state):
    ehandle = self.by_index[index]
    cls = self.fetch_cls(ehandle)
    dt = self.fetch_recv_table(ehandle).dt

    assert index in self.by_index
    assert ehandle in self.by_ehandle
    assert ehandle in self.by_cls[cls]
    assert ehandle in self.by_dt[dt]
    assert ehandle in self.classes

    self.by_ehandle[ehandle] = state

  def delete(self, index):
    ehandle = self.by_index[index]
    cls = self.fetch_cls(ehandle)
    dt = self.fetch_recv_table(ehandle).dt

    # no assertions because these will raise errors
    del self.by_index[index]
    del self.by_ehandle[ehandle]
    self.by_cls[cls].remove(ehandle)
    self.by_dt[dt].remove(ehandle)
    del self.classes[ehandle]

  def find(self, ehandle):
    return self.by_ehandle[ehandle]

  def find_index(self, index):
    ehandle = self.by_index[index]
    return self.find(ehandle)

  def find_all_by_cls(self, cls):
    coll = [(ehandle, self.find(ehandle)) for ehandle in self.by_cls[cls]]
    return collections.OrderedDict(coll)

  def find_by_cls(self, cls):
    try:
      return next(self.find_all_by_cls(cls).iteritems())
    except StopIteration:
      raise KeyError(cls)

  def find_all_by_dt(self, dt):
    coll = [(ehandle, self.find(ehandle)) for ehandle in self.by_dt[dt]]
    return collections.OrderedDict(coll)

  def find_by_dt(self, dt):
    try:
      return next(self.find_all_by_dt(dt).iteritems())
    except StopIteration:
      raise KeyError(dt)

  def fetch_cls(self, ehandle):
    return self.classes[ehandle]

  def fetch_recv_table(self, ehandle):
    return self.recv_tables[self.fetch_cls(ehandle)]
