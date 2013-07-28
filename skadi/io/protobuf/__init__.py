import math


VI_BIT_MAX = 32
VI_SHIFT = 7
VI_MAX_BYTES = int(math.ceil(float(VI_BIT_MAX) / VI_SHIFT))
VI_MASK = (1 << 32) - 1


class InvalidVarint32(Exception):
  pass


class InvalidProtobufMessage(Exception):
  pass


# Algorithm "borrowed" from Google protobuf library.
def peek_varint_32(io):
  peeked = io.peek(VI_MAX_BYTES)
  size, value, shift = 0, 0, 0

  while True:
    if size >= len(peeked):
      raise EOFError()

    byte = ord(peeked[size])
    size += 1
    value |= ((byte & 0x7f) << shift)
    shift += VI_SHIFT

    if not (byte & 0x80):
      value &= VI_MASK
      return value, size

    if shift >= VI_BIT_MAX:
      raise InvalidVarint32()


def read_varint_32(io):
  value, size = peek_varint_32(io)
  io.read(size)
  return value
