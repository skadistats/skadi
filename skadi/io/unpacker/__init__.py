try:
  from skadi.io import cBitstream as b_io
except ImportError:
  from skadi.io import bitstream as b_io


class UnpackComplete(RuntimeError):
  pass


class Unpacker(object):
  def __init__(self, bitstream):
    self.bitstream = bitstream

  def __iter__(self):
    def unpack():
      try:
        return self.unpack()
      except UnpackComplete:
        raise StopIteration()

    return iter(unpack, None)
