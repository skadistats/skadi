import collections


def construct(*args):
  return StringTable(*args)


class StringTable(object):
  def __init__(self, name, entry_bits, size_fixed, size_bits, entries):
    self.name = name
    self.entry_bits = entry_bits
    self.size_fixed = size_fixed
    self.size_bits = size_bits
    self.update_all(entries)

  def get(self, name):
    return self.by_name[name]

  def update_all(self, entries):
    mapped = map(lambda (i,n,d): (i,(n,d)), entries)
    self.by_index = collections.OrderedDict(mapped)

    mapped = map(lambda (i,n,d): (n,(i,d)), entries)
    self.by_name = collections.OrderedDict(mapped)

  def update(self, entry):
    i, n, d = entry

    if n:
      self.by_name[n] = (i, d)
      self.by_index[i] = (n, d)
    else:
      name, _ = self.by_index[i]
      self.by_name[n] = (i, d)
      self.by_index[i] = (n, d)
