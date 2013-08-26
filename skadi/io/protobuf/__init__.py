import collections

from skadi.protoc import demo_pb2 as pb_d


def parse(impl, message):
  pbmsg = impl()
  pbmsg.ParseFromString(message)
  return pbmsg


class ProtobufIO(object):
  class InvalidVarint(Exception):
    pass

  vi_max_bytes, vi_shift = 5, 7
  vi_mask = (1 << 32) - 1

  def __init__(self, _io):
    self.io = _io

  def __iter__(self):
    return iter(self.read, None)

  # via Google protobuf library
  def read_varint(self):
    size, value, shift = 0, 0, 0

    while True:
      try:
        byte = self.io.read(1)
        assert len(byte) == 1
      except AssertionError:
        raise EOFError()

      size += 1
      value |= (ord(byte) & 0x7f) << shift
      shift += ProtobufIO.vi_shift

      if not (ord(byte) & 0x80):
        value &= ProtobufIO.vi_mask
        return value

      if shift >= ProtobufIO.vi_shift * ProtobufIO.vi_max_bytes:
        raise ProtobufIO.InvalidVarint()
