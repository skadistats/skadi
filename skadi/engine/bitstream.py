import bitstring


SIZEOF_WORD_BYTES = 4
SIZEOF_WORD_BITS = SIZEOF_WORD_BYTES * 8
FORMAT = 'uintle:{0}'.format(SIZEOF_WORD_BITS)


def construct(bytes):
  return Bitstream(bytes)


class Bitstream(object):
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
    try:
      l = self.data[self.pos / SIZEOF_WORD_BITS]
      r = self.data[(self.pos + length - 1) / SIZEOF_WORD_BITS]
    except IndexError:
      raise EOFError('bitstream at end of data')

    pos_shift = self.pos & (SIZEOF_WORD_BITS - 1)
    rebuild = r << (SIZEOF_WORD_BITS - pos_shift) | l >> pos_shift

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

  def read_varint(self):
    run, value = 0, 0

    while True:
      bits = self.read(8)
      value |= (bits & 0x7f) << run
      run += 7

      if not (bits >> 7) or run == 35:
        break

    return value
