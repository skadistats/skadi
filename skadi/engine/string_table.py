import collections
import copy

from skadi.engine import bitstream as bs
from skadi.engine.unpacker import entity as uent
from skadi.engine.unpacker import string_table as ust


def construct(*args):
  return StringTable(*args)


class StringTable(object):
  def __init__(self, name, ent_bits, sz_fixed, sz_bits, ents, observer=None):
    self.name = name
    self.entry_bits = ent_bits
    self.size_fixed = sz_fixed
    self.size_bits = sz_bits
    self.observer = observer
    self.update_all(ents)

  def get(self, name):
    return self.by_name[name]

  def update_all(self, entries):
    self.by_index = collections.OrderedDict()
    self.by_name = collections.OrderedDict()

    if self.observer:
      self.observer.reset()

    [self.update(entry) for entry in entries]

  def update(self, entry):
    i, n, d = entry

    self.by_index[i] = (n, d)
    if n:
      self.by_name[n] = (i, d)

    if self.observer:
      self.observer.note((i, n, d))
