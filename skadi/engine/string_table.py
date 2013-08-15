import collections


MAX_NAME_LENGTH = 0x400
KEY_HISTORY_SIZE = 32


def unpack(bitstream, num_entries, entry_bits, ud_fixed_size, ud_size_bits):
  index, entries_read, entries = -1, 0, []
  key_history = collections.deque()

  option = bitstream.read(1)

  while entries_read < num_entries:
    consecutive = bitstream.read(1)
    index = index + 1 if consecutive else bitstream.read(entry_bits)

    name, value = None, ''

    has_name = bitstream.read(1)
    if has_name:
      assert not (option and bitstream.read(1)), 'unhandled serialization'

      additive = bitstream.read(1)
      if additive:
        basis, length = bitstream.read(5), bitstream.read(5)
        name = key_history[basis][0:length]
        name += bitstream.read_string(MAX_NAME_LENGTH - length);
      else:
        name = bitstream.read_string(MAX_NAME_LENGTH)

      if len(key_history) == KEY_HISTORY_SIZE:
        key_history.popleft()

      key_history.append(name)

    has_value = bitstream.read(1)
    if has_value:
      bit_length = ud_size_bits if ud_fixed_size else bitstream.read(14) * 8
      value = bitstream.read_long(bit_length)

    entries.append((index, name, value))
    entries_read += 1

  return entries
