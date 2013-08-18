import bitstring

from skadi.engine import unpacker
from skadi.engine.dt.prop import Flag, Type


def unpack(bitstream, props):
  return Unpacker(bitstream, props)


class Unpacker(unpacker.Unpacker):
  def __init__(self, bitstream, props):
    self.bitstream = bitstream
    self.props = props
    self._props_read = 0

  def unpack(self):
    if self._props_read == len(self.props):
      raise unpacker.UnpackComplete()

    prop = self.props[self._props_read]

    try:
      return self._actually_unpack(prop)
    finally:
      self._props_read += 1

    raise NotImplementedError('prop type {0}'.format(prop.type))

  def _actually_unpack(self, prop):
    if prop.type == Type.Int:
      return self._unpack_int(prop.flags, prop.num_bits)
    elif prop.type in (Type.Float, Type.Vector, Type.VectorXY):
      args = [prop.flags, prop.num_bits, prop.high_value, prop.low_value]
      if prop.type == Type.Float:
        fn = self._unpack_float
      elif prop.type == Type.Vector:
        fn = self._unpack_vector
      elif prop.type == Type.VectorXY:
        fn = self._unpack_vectorxy
      return fn(*args)
    elif prop.type == Type.String:
      return self._unpack_string()
    elif prop.type == Type.Array:
      return self._unpack_array(prop.num_elements, prop.array_prop)
    elif prop.type == Type.Int64:
      return self._unpack_int64(prop.flags, prop.num_bits)

  def _unpack_int(self, flags, num_bits):
    if flags & Flag.EncodedAgainstTickcount:
      if flags & Flag.Unsigned:
        return self.bitstream.read_varint()
      else:
        value = self.bitstream.read_varint()
        return (-(value & 1)) ^ (value >> 1)

    value = self.bitstream.read(num_bits)
    l = 0x80000000 >> (32 - num_bits)
    r = (flags & Flag.Unsigned) - 1

    return (value ^ (l & r)) - (l & r)

  def _unpack_float(self, flags, num_bits, high_value, low_value):
    if flags & Flag.Coord:
      integer = self.bitstream.read(1)
      fraction = self.bitstream.read(1)

      if not integer and not fraction:
        return 0.0

      negate = self.bitstream.read(1)

      if integer:
        integer = self.bitstream.read(0x0e) + 1

      if fraction:
        fraction = self.bitstream.read(5)

      value = 0.03125 * fraction
      value += integer

      if negate:
        value *= -1

      return value
    elif flags & Flag.NoScale:
      bit_array = bitstring.BitArray(uint=self.bitstream.read(32), length=32)
      return bit_array.float
    elif flags & Flag.Normal:
      sign = self.bitstream.read(1)
      bit_array = bitstring.BitArray(uint=self.bitstream.read(11), length=32)

      value = bit_array.float
      if (bit_array >> 31):
        value += 4.2949673e9
      value *= 4.885197850512946e-4
      if sign:
        value *= -1

      return value
    elif flags & Flag.CellCoord:
      value = self.bitstream.read(num_bits)
      return value + 0.03125 * self.bitstream.read(5)
    elif flags & Flag.CellCoordIntegral:
      value = self.bitstream.read(num_bits)
      if value >> 31:
        value += 4.2949673e9 # wat, edith?
      return float(value)

    dividend = self.bitstream.read(num_bits);
    divisor = (1 << num_bits) - 1;

    f = float(dividend) / divisor
    r = high_value - low_value
    return f * r + low_value;

  def _unpack_vector(self, flags, num_bits, high_value, low_value):
    x = self._unpack_float(flags, num_bits, high_value, low_value)
    y = self._unpack_float(flags, num_bits, high_value, low_value)

    if flags & Flag.Normal:
      f = x * x + y * y
      z = 0 if (f <= 1) else math.sqrt(1 - f)

      sign = self.bitstream.read(1)
      if sign:
        z *= -1
    else:
      z = self._unpack_float(flags, num_bits, high_value, low_value)

    return x, y, z

  def _unpack_vectorxy(self, flags, num_bits, high_value, low_value):
    x = self._unpack_float(flags, num_bits, high_value, low_value)
    y = self._unpack_float(flags, num_bits, high_value, low_value)
    return x, y

  def _unpack_string(self):
    return self.bitstream.read_string(self.bitstream.read(9))

  def _unpack_array(self, num_elements, array_prop):
    n, bits = num_elements, 0

    while n:
      bits += 1
      n >>= 1

    count, i, elements = self.bitstream.read(bits), 0, []

    while i < count:
      elements.append(self._actually_unpack(array_prop))
      i += 1

    return elements

  def _unpack_int64(self, flags, num_bits):
    if flags & Flag.EncodedAgainstTickcount:
      raise NotImplementedError('int64 cant be encoded against tickcount')

    negate = False
    second_bits = num_bits - 32

    if not (flags & Flag.Unsigned):
      second_bits -= 1
      if self.bitstream.read(1):
        negate = True

    a = self.bitstream.read(32)
    b = self.bitstream.read(second_bits)

    value = (a << 32) | b
    if negate:
      value *= -1

    return value
