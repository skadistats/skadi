import collections

from skadi import enum
from skadi.domain import string_table as d_st

Flag = enum(Unknown = 0x01, ProbablyPrecache = 0x02, FixedLength = 0x08)

MAX_NAME_LENGTH = 0x400
KEY_HISTORY_SIZE = 32

def read(io, string_table, num_entries = None):
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
      entries.append(d_st.String(name, value))

    entries_read += 1

  return entries
