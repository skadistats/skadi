from skadi.engine import unpacker


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
      if prop.type == dt_prop.Type.Int:
        return self._unpack_int(prop.flags, prop.num_bits)
      elif prop.type in (prop.Type.Float, prop.Type.Vector, prop.Type.VectorXY):
        args = [prop.flags, prop.num_bits, prop.high_value, prop.low_value]
        if prop.type == prop.Type.Float:
          fn = self._unpack_float
        elif prop.type == prop.Type.Vector:
          fn = self._unpack_vector
        elif prop.type == prop.Type.VectorXY:
          fn = self._unpack_vectorxy
        return fn(*args)
      elif prop.type == prop.Type.String:
        return self._unpack_string()
      elif prop.type == prop.Type.Array:
        return self._unpack_array(prop.num_elements, prop.array_prop)
      elif prop.type == prop.Type.Int64:
        return self._unpack_int64(prop.flags, prop.num_bits)
    finally:
      self._props_read += 1

    raise NotImplementedError('prop type {0}'.format(prop.type))

  def _unpack_int(self, flags, num_bits):
    if flags & dt_prop.Flag.EncodedAgainstTickcount:
      if flags & dt_prop.Flag.Unsigned:
        return self.self.bitstream.read_varint()
      else:
        value = self.self.bitstream.read_varint()
        return (-(value & 1)) ^ (value >> 1)

    value = self.self.bitstream.read(num_bits)
    l = 0x80000000 >> (32 - num_bits)
    r = (flags & dt_prop.Flag.Unsigned) - 1

    return (value ^ (l & r)) - (l & r)

  def _unpack_float(self, flags, num_bits, high_value, low_value):
    if flags & dt_prop.Flag.Coord:
      integer = self.self.bitstream.read(1)
      fraction = self.self.bitstream.read(1)

      if not integer and not fraction:
        return 0.0

      negate = self.self.bitstream.read(1)

      if integer:
        integer = self.self.bitstream.read(0x0e) + 1

      if fraction:
        fraction = self.self.bitstream.read(5)

      value = 0.03125 * fraction
      value += integer

      if negate:
        value *= -1

      return value
    elif flags & dt_prop.Flag.NoScale:
      bit_array = bitstring.BitArray(uint=self.self.bitstream.read(32), length=32)
      return bit_array.float
    elif flags & dt_prop.Flag.Normal:
      sign = self.self.bitstream.read(1)
      bit_array = bitstring.BitArray(uint=self.self.bitstream.read(11), length=32)

      value = bit_array.float
      if (bit_array >> 31):
        value += 4.2949673e9
      value *= 4.885197850512946e-4
      if sign:
        value *= -1

      return value
    elif flags & dt_prop.Flag.CellCoord:
      value = self.self.bitstream.read(p.num_bits)
      return value + 0.03125 * self.self.bitstream.read(5)
    elif flags & dt_prop.Flag.CellCoordIntegral:
      value = self.self.bitstream.read(p.num_bits)
      if value >> 31:
        value += 4.2949673e9 # wat, edith?
      return float(value)
    else:
      raise NotImplementedError('unsupported serialization')

    dividend = self.self.bitstream.read(num_bits);
    divisor = (1 << num_bits) - 1;

    f = float(dividend) / divisor
    r = high_value - low_value
    return f * r + low_value;

  def _unpack_vector(self, flags, num_bits, high_value, low_value):
    x = self._unpack_float(flags, num_bits, high_value, low_value)
    y = self._unpack_float(flags, num_bits, high_value, low_value)

    if flags & dt_prop.Flag.Normal:
      f = x * x + y * y
      z = 0 if (f <= 1) else math.sqrt(1 - f)

      sign = self.self.bitstream.read(1)
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
    return self.self.bitstream.read_string(self.self.bitstream.read(9))

  def _unpack_array(self, num_elements, array_prop):
    n, bits = num_elements, 0
    while n:
      bits += 1
      n >>= 1

    count, i, elements = self.self.bitstream.read(bits), 0, []
    while i < count:
      elements.append(self._unpack(array_prop))
      i += 1

    return elements

  def _unpack_int64(self, flags, num_bits):
    if flags & dt_prop.Flag.EncodedAgainstTickcount:
      raise NotImplementedError('int64 cant be encoded against tickcount')

    negate = False
    second_bits = num_bits - 32

    if not (flags & dt_prop.Flag.Unsigned):
      second_bits -= 1
      if self.self.bitstream.read(1):
        negate = True

    a = self.self.bitstream.read(32)
    b = self.self.bitstream.read(second_bits)

    value = (a << 32) | b
    if negate:
      value *= -1

    return value
