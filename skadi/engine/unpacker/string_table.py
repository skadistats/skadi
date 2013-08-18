import collections

from skadi.engine import unpacker


MAX_NAME_LENGTH = 0x400
KEY_HISTORY_SIZE = 32


def unpack(*args):
  return Unpacker(*args)


class Unpacker(unpacker.Unpacker):
  def __init__(self, bitstream, num_ent, ent_bits, sz_fixed, sz_bits):
    super(Unpacker, self).__init__(bitstream)
    self.num_entries = num_ent
    self.entry_bits = ent_bits
    self.size_fixed = sz_fixed
    self.size_bits = sz_bits
    self._option = self.bitstream.read(1)
    self._key_history = collections.deque()
    self._index = -1
    self._entries_read = 0

  def unpack(self):
    if self._entries_read == self.num_entries:
      raise unpacker.UnpackComplete()

    consecutive = self.bitstream.read(1)
    if consecutive:
      self._index += 1
    else:
      self._index = self.bitstream.read(self.entry_bits)

    name, value = None, ''

    has_name = self.bitstream.read(1)
    if has_name:
      assert not (self._option and self.bitstream.read(1))

      additive = self.bitstream.read(1)

      if additive:
        basis, length = self.bitstream.read(5), self.bitstream.read(5)
        name = self._key_history[basis][0:length]
        name += self.bitstream.read_string(MAX_NAME_LENGTH - length);
      else:
        name = self.bitstream.read_string(MAX_NAME_LENGTH)

      if len(self._key_history) == KEY_HISTORY_SIZE:
        self._key_history.popleft()

      self._key_history.append(name)

    has_value = self.bitstream.read(1)
    if has_value:
      if self.size_fixed:
        bit_length = self.size_bits
      else:
        bit_length = self.bitstream.read(14) * 8

      value = self.bitstream.read_long(bit_length)

    self._entries_read += 1

    return self._index, name, value
