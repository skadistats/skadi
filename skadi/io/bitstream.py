import bitstring
import io
import pdb

PVS_ENT = 0b001
PVS_BYE = 0b010
PVS_DEL = 0b100

SIZEOF_BYTE = 4
SIZEOF_BIT = SIZEOF_BYTE * 8
FORMAT = 'uintle:{0}'.format(SIZEOF_BIT)

class EntityHeaderUnavailable(EOFError):
  pass

class BitstreamIO(object):
  @classmethod
  def wrapping(cls, bytes):
    return cls(bytes)

  def __init__(self, bytes):
    self.pos = 0
    self.data = []

    remainder = len(bytes) % 4
    if remainder:
      bytes = bytes + '\0' * (4 - remainder)

    bs = bitstring.ConstBitStream(bytes=bytes)
    while True:
      try:
        word = bs.read('uintle:32')
        self.data.append(word)
      except bitstring.ReadError:
        break

  def read(self, length): # in bits
    l = self.data[self.pos / SIZEOF_BIT]
    r = self.data[(self.pos + length - 1) / SIZEOF_BIT]

    pos_shift = self.pos & (SIZEOF_BIT - 1)
    rebuild = r << (SIZEOF_BIT - pos_shift) | l >> pos_shift

    self.pos += length

    return rebuild & ((1 << length) - 1)

  def read_string(self, length):
    remaining, i, bytes = length, 0, []

    while remaining >= 8:
      bytes.append(self.read(8))
      remaining -= 8
    if remaining:
      bytes.append(self.read(remaining))

    return str(bytearray(bytes))

  def read_varint_35(self):
    run, value = 0, 0

    while True:
      bits = self.read(8)
      value |= (bits & 0x7f) << run
      run += 7

      if not (bits >> 7) or run == 28:
        break

    return value

  def read_entity_header(self, base_ent_index):
    try:
      value = self.read(6)

      if value & 0x30:
        a = (value >> 4) & 3
        b = 16 if a == 3 else 0
        value = self.read(4 * a + b) << 4 | (value & 0xf)

      flags = 0
      if not self.read(1):
        if self.read(1):
          flags |= PVS_ENT
      else:
        flags |= PVS_BYE
        if self.read(1):
          flags |= PVS_DEL
    except IndexError:
      raise EntityHeaderUnavailable()

    return base_ent_index + value + 1, flags

  def read_entity_delta_props(self):
    edp, cursor = [], -1
    while True:
      consecutive = self.read(1)
      if consecutive:
        cursor += 1
      else:
        offset = self.read_varint_35()
        if offset == 0x3fff:
          return edp
        else:
          cursor += offset + 1
      edp.append(cursor)
