import math

class String(object):
  def __init__(self, name, data):
    self.name = name
    self.data = data

  def __repr__(self):
    n, d = self.name, self.data
    return "<String '{0}' ({1} bytes)>".format(n, len(d))

class StringTable(object):
  def __init__(self, name, max_ent, num_ent, udfs, uds, udsb, flags, items=None):
    self.name = name
    self.max_entries = max_ent
    self.num_entries = num_ent
    self.user_data_fixed_size = udfs
    self.user_data_size = uds
    self.user_data_size_bits = udsb
    self.flags = flags
    self.items = items

    self.entry_bits = int(math.ceil(math.log(self.max_entries, 2)))

  def __repr__(self):
    n, f = self.name, hex(int(self.flags))
    lenitems = len(self.items)
    lenitemsc = len(self.items_clientside)
    _repr = "<StringTable '{0}' f:{1} ({2} items, {3} items clientside)"
    return _repr.format(n, f, lenitems, lenitemsc)

  def __getitem__(self, key):
    gen = (i for i in self.items if i.name == key)
    return next(gen, None)