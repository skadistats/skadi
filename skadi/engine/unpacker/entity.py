from skadi import enum
from skadi.engine import unpacker
from skadi.engine.unpacker import prop as pu


PVS = enum(Preserving = 0, Entering = 0x01, Deleting = 0x04)


class Unpacker(unpacker.Unpacker):
  def __init__(self, bitstream, b_ind, ct, delt, cls_bits, recv_tables, ents):
    super(Unpacker, self).__init__(bitstream)
    self.base_index = b_ind
    self.count = ct
    self.is_delta = delt
    self.class_bits = cls_bits
    self.recv_tables = recv_tables
    self.entities = ents
    self._index = -1
    self._entities_read = 0

  def unpack(self):
    if self._entities_read == self.count:
      try:
        deletion = self.bitstream.read(1)
        if deletion:
          return PVS.Deleting, self.bitstream.read(10)
        return
      except EOFError:
        raise unpacker.UnpackComplete()

    try:
      self._index, mode = self._read_header()
      if mode & PVS.Entering:
        cls = str(self.bitstream.read(self.class_bits))
        serial = self.bitstream.read(10)
        prop_list = self._read_prop_list()
        delta = self._read_delta(prop_list, self.recv_tables[cls])

        return PVS.Entering, self._index, (cls, serial, delta)
      elif mode & PVS.Deleting:
        return PVS.Deleting, self._index, ()

      # otherwise, we're "preserving" (aka "updating") the entity
      cls = self.entities[self._index][0]
      delta = self._read_delta(self.read_prop_list(), self.recv_tables[cls])
      prop_list = self._read_prop_list()
      delta = self._read_delta(prop_list, self.recv_tables[cls])

      return PVS.Preserving, self._index, (delta,)
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

    mode = PVS.Preserving

    if not self.bitstream.read(1):
      if self.bitstream.read(1):
        mode = PVS.Entering
    elif self.bitstream.read(1):
      mode = PVS.Deleting

    return self._index + encoded_index + 1, mode

  def _read_prop_list(self):
    prop_list, cursor = [], -1

    while True:
      consecutive = self.bitstream.read(1)

      if consecutive:
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
    packet_unpacker = pu.Unpacker(self.bitstream, props)
    delta = {}

    try:
      for prop in props:
        key = '{0}.{1}'.format(prop.origin_dt, prop.var_name)
        delta[key] = packet_unpacker.unpack()
    except unpacker.UnpackComplete:
      print key
      raise RuntimeError()

    return delta
