import math


VI_BIT_MAX = 35
VI_SHIFT = 7
VI_MAX_BYTES = int(math.ceil(float(VI_BIT_MAX) / VI_SHIFT))
VI_MASK = (1 << 32) - 1


class InvalidVarint(Exception):
  pass


# Algorithm "borrowed" from Google protobuf library.
def peek_varint(stream):
  peeked = stream.peek(VI_MAX_BYTES)
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
      raise InvalidVarint


def read_varint(stream):
  value, size = peek_varint(stream)
  stream.read(size)
  return value


class InvalidProtobufMessage(Exception):
  pass


class Index(object):
  def __init__(self, iterable):
    self.peeks = list(iterable)

  def __iter__(self):
    return iter(self.peeks)

  def find(self, cls):
    return next(iter(filter(lambda p: p.cls == cls, self.peeks)), None)

  def find_all(self, cls):
    return filter(lambda p: p.cls == cls, self.peeks)

  def find_behind(self, offset):
    return filter(lambda p: p.offset < offset, self.peeks)

  def find_at(self, offset):
    return filter(lambda p: p.offset == offset, self.peeks)

  def find_ahead(self, offset):
    return filter(lambda p: p.offset > offset, self.peeks)
