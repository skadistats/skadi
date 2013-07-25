import collections
import math

from skadi import enum
from skadi.io import bitstream as io_bs

Flag = enum(Unknown = 0x01, ProbablyPrecache = 0x02, FixedLength = 0x08)

MAX_NAME_LENGTH = 0x400
KEY_HISTORY_SIZE = 32


def decode(io, string_table, num_entries = None):
  if num_entries is None:
    num_entries = string_table.num_entries

  index, entries_read, entries = -1, 0, []
  key_history = collections.deque()

  first = io.read(1)

  while entries_read < num_entries:
    consecutive = io.read(1)
    if not consecutive:
      index = io.read(string_table.entry_bits)
    else:
      index += 1

    name = None

    if io.read(1):
      if first and io.read(1):
        raise NotImplementedError('code path #1')
      else:
        substring = io.read(1)
        if substring:
          index, until = io.read(5), io.read(5)
          name = key_history[index][0:until]
          name += io.read_string(MAX_NAME_LENGTH - until);
        else:
          name = io.read_string(MAX_NAME_LENGTH)

        if len(key_history) == KEY_HISTORY_SIZE:
          key_history.popleft()
        key_history.append(name)

    if io.read(1):
      if string_table.user_data_fixed_size:
        bit_length = string_table.user_data_size_bits
      else:
        length = io.read(14)
        bit_length = length * 8

      value = io.read_long(bit_length)
      entries.append(String(name, value))

    entries_read += 1

  return entries


def parse(pbmsg):
  name, flags = pbmsg.name, pbmsg.flags
  me, ne = pbmsg.max_entries, pbmsg.num_entries
  udfs = pbmsg.user_data_fixed_size
  uds, udsb = pbmsg.user_data_size, pbmsg.user_data_size_bits

  st = StringTable(name, me, ne, udfs, uds, udsb, flags)
  st.items = decode(io_bs.Bitstream(pbmsg.string_data), st)

  return st


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
    _repr = "<StringTable '{0}' f:{1} ({2} items)"
    return _repr.format(n, f, lenitems)

  def __getitem__(self, key):
    gen = (i for i in self.items if i.name == key)
    return next(gen, None)