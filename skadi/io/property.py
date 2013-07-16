import bitstring
import math
import sys

from skadi.state.dt import Flag, Type

TYPE_EXCLUSIONS = ('DataTable')
BY_TYPE = {v:k for k,v in Type.tuples.items() if k not in TYPE_EXCLUSIONS}

class Reader(object):
  @classmethod
  def read(cls, prop, io):
    _type = BY_TYPE[prop.type]
    reader_cls = '{0}Reader'.format(_type)
    return getattr(sys.modules[__name__], reader_cls)(prop, io).read()

  def __init__(self, prop, io):
    self.prop = prop
    self.io = io

class IntReader(Reader):
  def __init__(self, prop, io):
    super(IntReader, self).__init__(prop, io)

  def read(self):
    if self.prop.flags & Flag.EncodedAgainstTickcount:
      if self.prop.flags & Flag.Unsigned:
        return self.io.read_varint_35()
      else:
        value = self.io.read_varint_35()
        return (-(value & 1)) ^ (value >> 1)

    value = self.io.read(self.prop.num_bits)
    l = 0x80000000 >> (32 - self.prop.num_bits)
    r = (self.prop.flags & Flag.Unsigned) - 1

    return (value ^ (l & r)) - (l & r)

class FloatReader(Reader):
  def __init__(self, prop, io):
    super(FloatReader, self).__init__(prop, io)

  def read(self):
    if self.prop.flags & Flag.Coord:
      integer = self.io.read(1)
      fraction = self.io.read(1)

      if not integer and not fraction:
        return 0.0

      negate = self.io.read(1)

      if integer:
        integer = self.io.read(0x0e) + 1

      if fraction:
        fraction = self.io.read(5)

      value = 0.03125 * fraction
      value += integer

      if negate:
        value *= -1

      return value
    elif self.prop.flags & Flag.CoordMP:
      raise NotImplementedError('! CoordMP')
    elif self.prop.flags & Flag.CoordMPLowPrecision:
      raise NotImplementedError('! CoordMPLowPrecision')
    elif self.prop.flags & Flag.CoordMPIntegral:
      raise NotImplementedError('! CoordMPIntegral')
    elif self.prop.flags & Flag.NoScale:
      bit_array = bitstring.BitArray(uint=self.io.read(32), length=32)
      return bit_array.float
    elif self.prop.flags & Flag.Normal:
      sign = self.io.read(1)
      bit_array = bitstring.BitArray(uint=self.io.read(11), length=32)

      value = bit_array.float
      if (bit_array >> 31):
        value += 4.2949673e9
      value *= 4.885197850512946e-4
      if sign:
        value *= -1

      return value
    elif self.prop.flags & Flag.CellCoord:
      value = self.io.read(self.prop.num_bits)
      return value + 0.03125 * self.io.read(5)
    elif self.prop.flags & Flag.CellCoordLowPrecision:
      raise NotImplementedError('! CellCoordLowPrecision')
    elif self.prop.flags & Flag.CellCoordIntegral:
      value = self.io.read(self.prop.num_bits)
      if value >> 31:
        value += 4.2949673e9 # wat, edith?
      return float(value)

    dividend = self.io.read(self.prop.num_bits);
    divisor = (1 << self.prop.num_bits) - 1;

    f = float(dividend) / divisor
    r = self.prop.high_value - self.prop.low_value

    return f * r + self.prop.low_value;

class VectorReader(Reader):
  def __init__(self, prop, io):
    super(VectorReader, self).__init__(prop, io)

  def read(self):
    x = FloatReader(self.prop, self.io).read()
    y = FloatReader(self.prop, self.io).read()

    if self.prop.flags & Flag.Normal:
      f = x * x + y * y
      z = 0 if (f <= 1) else math.sqrt(1 - f)

      sign = self.io.read(1)
      if sign:
        z *= -1
    else:
      z = FloatReader(self.prop, self.io).read()

    return x, y, z

class VectorXYReader(Reader):
  def __init__(self, prop, io):
    super(VectorXYReader, self).__init__(prop, io)

  def read(self):
    x = FloatReader(self.prop, self.io).read()
    y = FloatReader(self.prop, self.io).read()
    return x, y

class StringReader(Reader):
  def __init__(self, prop, io):
    super(StringReader, self).__init__(prop, io)

  def read(self):
    length = self.io.read(9)
    return self.io.read_string(length * 8)

class ArrayReader(Reader):
  def __init__(self, prop, io):
    super(ArrayReader, self).__init__(prop, io)

  def read(self):
    n, bits = self.prop.num_elements, 0
    while n:
      bits += 1
      n >>= 1

    count, i, elements = self.io.read(bits), 0, []
    while i < count:
      elements.append(Reader.read(self.prop.array_prop, self.io))
      i += 1

    return elements

class Int64Reader(Reader):
  def __init__(self, prop, io):
    super(Int64Reader, self).__init__(prop, io)

  def read(self):
    if self.prop.flags & Flag.EncodedAgainstTickcount:
      raise NotImplementedError('int64 cant be encoded against tickcount')

    negate = False
    second_bits = self.prop.num_bits - 32

    if not (self.prop.flags & Flag.Unsigned):
      second_bits -= 1
      if self.io.read(1):
        negate = True

    a = self.io.read(32)
    b = self.io.read(second_bits)

    value = (a << 32) | b
    if negate:
      value *= -1

    return value