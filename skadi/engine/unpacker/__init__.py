

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
