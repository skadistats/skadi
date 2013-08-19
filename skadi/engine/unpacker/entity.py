from skadi import enum
from skadi.engine import unpacker
from skadi.engine.unpacker import prop as pu


PVS = enum(Leaving = 1, Entering = 2, Deleting = 4)


def unpack(*args):
  return Unpacker(*args)


class Unpacker(unpacker.Unpacker):
  def __init__(self, bitstream, base_index, count, delta, class_bits, world):
    super(Unpacker, self).__init__(bitstream)
    self.base_index = base_index
    self.count = count
    self.is_delta = delta
    self.class_bits = class_bits
    self.world = world
    self._index = -1
    self._entities_read = 0

  def unpack(self):
    if self._entities_read == self.count:
      if not self.is_delta:
        raise unpacker.UnpackComplete()
      try:
        if self.bitstream.read(1):
          return PVS.Deleting, self.bitstream.read(11), ()
      except EOFError:
        raise unpacker.UnpackComplete()

    try:
      self._index, mode = self._read_header()

      if mode & PVS.Entering:
        cls = str(self.bitstream.read(self.class_bits))
        serial = self.bitstream.read(10)
        rt = self.world.recv_tables[cls]
        delta = self._read_delta(self._read_prop_list(), rt)

        context = (cls, serial, delta)
      elif mode & PVS.Leaving:
        context = ()
      else:
        rt = self.world.fetch_recv_table(self.world.by_index[self._index])
        context = self._read_delta(self._read_prop_list(), rt)

      return self._index, mode, context

    finally:
      self._entities_read += 1

  def unpack_baseline(self, recv_table):
    prop_list = self._read_prop_list()
    return self._read_delta(prop_list, recv_table)

  def _read_header(self):
    encoded_index = self.bitstream.read(6)

    if encoded_index & 0x30:
      a = (encoded_index >> 0x04) & 0x03
      b = 16 if a == 0x03 else 0
      encoded_index = \
        self.bitstream.read(4 * a + b) << 4 | (encoded_index & 0x0f)

    mode = 0
    if not self.bitstream.read(1):
      if self.bitstream.read(1):
        mode |= PVS.Entering
    else:
      mode |= PVS.Leaving
      if self.bitstream.read(1):
        mode |= PVS.Deleting

    return self._index + encoded_index + 1, mode

  def _read_prop_list(self):
    prop_list, cursor = [], -1

    while True:
      if self.bitstream.read(1):
        cursor += 1
      else:
        offset = self.bitstream.read_varint()
        if offset == 0x3fff:
          return prop_list
        else:
          cursor += offset + 1

      prop_list.append(cursor)

  def _read_delta(self, prop_list, recv_table):
    props = [recv_table.props[i] for i in prop_list]
    unpacker = pu.Unpacker(self.bitstream, props)

    return {(p.origin_dt, p.var_name):unpacker.unpack() for p in props}
