import collections
import copy
import math

from skadi import enum
from skadi.io import bitstream as bitstream_io


Flag = enum(Unknown = 0x01, ProbablyPrecache = 0x02, FixedLength = 0x08)


class String(object):
  def __init__(self, name, data):
    self.name = name
    self.data = data

  def __copy__(self):
    return String(self.name, self.data)

  def __repr__(self):
    n, d = self.name, self.data
    return "<String '{0}' ({1} bytes)>".format(n, len(d or ''))


class StringTable(object):
  def __init__(self, name, max_ent, num_ent, udfs, uds, udsb, flags, ii=None):
    self.name = name
    self.max_entries = max_ent
    self.num_entries = num_ent
    self.user_data_fixed_size = udfs
    self.user_data_size = uds
    self.user_data_size_bits = udsb
    self.flags = flags
    self.items = ii or collections.OrderedDict()

    self.entry_bits = int(math.ceil(math.log(self.max_entries, 2)))

  def __copy__(self):
    name = self.name
    max_ent = self.max_entries
    num_ent = self.num_entries
    udfs = self.user_data_fixed_size
    uds = self.user_data_size
    udsb = self.user_data_size_bits
    flags = self.flags
    ii = copy.copy(self.items)

    return StringTable(name, max_ent, num_ent, udfs, uds, udsb, flags, ii)

  def __repr__(self):
    n, f = self.name, hex(int(self.flags))
    lenitems = len(self.items)
    _repr = "<StringTable '{0}' f:{1} ({2} items)"
    return _repr.format(n, f, lenitems)

  def __getitem__(self, key):
    gen = (i for i in self.items if i.name == key)
    return next(gen, None)

  def merge(self, strings):
    st = copy.copy(self)

    for name, data in strings:
      st.items[name] = String(name, data)

    return st
