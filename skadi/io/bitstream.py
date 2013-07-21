import bitstring
import io

SIZEOF_BYTE = 4
SIZEOF_BIT = SIZEOF_BYTE * 8
FORMAT = 'uintle:{0}'.format(SIZEOF_BIT)

class Bitstream(object):
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

  def read_long(self, length):
    remaining, bytes = length, []
    while remaining > 7:
      remaining -= 8
      bytes.append(self.read(8))
    if remaining:
      bytes.append(self.read(remaining))
    return str(bytearray(bytes))

  def read_string(self, length):
    i, bytes = 0, []
    while i < length:
      byte = self.read(8)
      if byte == 0:
        return str(bytearray(bytes))
      bytes.append(byte)
      i += 1
    return str(bytearray(bytes))

  def read_varint_35(self):
    run, value = 0, 0

    while True:
      bits = self.read(8)
      value |= (bits & 0x7f) << run
      run += 7

      if not (bits >> 7) or run == 35:
        break

    return value
