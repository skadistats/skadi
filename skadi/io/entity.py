from skadi import enum

PVS = enum(Enter = 0x01, Leave = 0x02, Delete = 0x04)

class HeaderReader(object):
  def __init__(self, io):
    self.io = io

  def read(self, base_index):
    try:
      index = self.io.read(6)
      if index & 0x30:
        a = (index >> 0x04) & 0x03
        b = 16 if a == 0x03 else 0
        index = self.io.read(4 * a + b) << 4 | (index & 0x0f)

      flags = 0
      if not self.io.read(1):
        if self.io.read(1):
          flags |= PVS.Enter
      else:
        flags |= PVS.Leave
        if self.io.read(1):
          flags |= PVS.Delete
    except IndexError:
      raise ReadError('unable to read entity header')

    return base_index + index + 1, flags

class PropListReader(object):
  def __init__(self, io):
    self.io = io

  def read(self):
    dp, cursor = [], -1
    while True:
      consecutive = self.io.read(1)
      if consecutive:
        cursor += 1
      else:
        offset = self.io.read_varint_35()
        if offset == 0x3fff:
          return dp
        else:
          cursor += offset + 1
      dp.append(cursor)

class EnterPVSPreludeReader(object):
  def __init__(self, io):
    self.io = io

  def read(self, class_bits):
    plr = PropListReader(self.io)
    return self.io.read(class_bits), self.io.read(10), plr.read()
