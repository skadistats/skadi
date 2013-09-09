from libc.stdint cimport *
from skadi.io cimport cBitstream as bs

import math

from skadi.io import unpacker

from skadi.engine.dt.consts cimport *

def construct(bitstream, props):
  return Unpacker(bitstream, props)

# If sizeof(float) != sizeof(uint32_t), then we're all fucked. But
# it's worth checking that via an assert before using this
cdef union UIntOrFloat:
  float asFloat
  uint32_t asUInt

cdef class Unpacker(object):
  cdef public bs.Bitstream bitstream
  cdef public object props
  cdef int _props_read

  def __init__(self, bitstream, props):
    self.bitstream = bitstream
    self.props = props
    self._props_read = 0

  def unpack(self):
    return self._unpack()

  cdef object _unpack(Unpacker self):
    if self._props_read == len(self.props):
      raise unpacker.UnpackComplete()

    cdef object prop
    prop = self.props[self._props_read]

    try:
      return self._actually_unpack(prop)
    finally:
      self._props_read += 1

  cdef object _actually_unpack(Unpacker self, object prop):
    cdef char type_ = prop.type
    if type_ == INT:
      return self._unpack_int(prop.flags, prop.num_bits)
    elif type_ == FLOAT:
      return self._unpack_float(prop.flags, prop.num_bits,
                                prop.high_value, prop.low_value)
    elif type_ == VECTOR:
      return self._unpack_vector(prop.flags, prop.num_bits,
                                 prop.high_value, prop.low_value)
    elif type_ == VECTORXY:
      return self._unpack_vectorxy(prop.flags, prop.num_bits,
                                   prop.high_value, prop.low_value)
    elif type_ == STRING:
      return self._unpack_string()
    elif type_ == ARRAY:
      return self._unpack_array(prop.num_elements, prop.array_prop)
    elif type_ == INT64:
      return self._unpack_int64(prop.flags, prop.num_bits)

    raise NotImplementedError('prop type {0}'.format(prop.type))

  cdef int _unpack_int(Unpacker self, int flags, int num_bits):
    cdef int64_t value, l, r

    if flags & ENCODEDAGAINSTTICKCOUNT:
      if flags & UNSIGNED:
        return self.bitstream._read_varint()
      else:
        value = self.bitstream._read_varint()
        return (-(value & 1)) ^ (value >> 1)

    value = self.bitstream._read(num_bits)
    l = 0x80000000 >> (32 - num_bits)
    r = (flags & UNSIGNED) - 1

    return (value ^ (l & r)) - (l & r)

  cdef float _unpack_float(Unpacker self, uint64_t flags, int num_bits,
                           int high_value, int low_value):
#    assert bool(sizeof(uint32_t) == sizeof(float)), \
#      "sizeof(float) != sizeof(uint32_t). Petition for a float32_t type."
    cdef UIntOrFloat float_conv

    cdef int integer, fraction, negate
    cdef float value

    if flags & COORD:
      integer = self.bitstream._read(1)
      fraction = self.bitstream._read(1)

      if not integer and not fraction:
        return 0.0

      negate = self.bitstream._read(1)

      if integer:
        integer = self.bitstream._read(0x0e) + 1

      if fraction:
        fraction = self.bitstream._read(5)

      value = 0.03125 * fraction
      value += integer

      if negate:
        value *= -1

      return value
    elif flags & NOSCALE:
      float_conv.asUInt = self.bitstream._read(32)
      return float_conv.asFloat
    elif flags & NORMAL:
      sign = self.bitstream._read(1)
      float_conv.asUInt = self.bitstream._read(11)

      value = float_conv.asFloat
      if float_conv.asUInt >> 31:
        value += 4.2949673e9
      value *= 4.885197850512946e-4
      if sign:
        value *= -1

      return value
    elif flags & CELLCOORD:
      value = self.bitstream._read(num_bits)
      return value + 0.03125 * self.bitstream._read(5)
    elif flags & CELLCOORDINTEGRAL:
      raw = self.bitstream._read(num_bits)
      if raw >> 31:
        value = raw + 4.2949673e9 # wat, edith?
      return value

    cdef int dividend, divisor
    dividend = self.bitstream._read(num_bits)
    divisor = (1 << num_bits) - 1

    cdef float f
    f = <float>dividend / divisor
    r = high_value - low_value
    return f * r + low_value

  cdef object _unpack_vector(Unpacker self, uint64_t flags, int num_bits,
                             int high_value, int low_value):
    cdef float x, y, f, z
    cdef int sign
    x = self._unpack_float(flags, num_bits, high_value, low_value)
    y = self._unpack_float(flags, num_bits, high_value, low_value)

    if flags & NORMAL:
      f = x * x + y * y
      z = 0 if (f <= 1) else math.sqrt(1 - f)

      sign = self.bitstream._read(1)
      if sign:
        z *= -1
    else:
      z = self._unpack_float(flags, num_bits, high_value, low_value)

    return x, y, z

  cdef object _unpack_vectorxy(Unpacker self, uint64_t flags, int num_bits,
                               int high_value, int low_value):
    cdef float x, y
    x = self._unpack_float(flags, num_bits, high_value, low_value)
    y = self._unpack_float(flags, num_bits, high_value, low_value)
    return x, y

  cdef object _unpack_string(Unpacker self):
    return self.bitstream._read_string(self.bitstream._read(9))

  cdef object _unpack_array(Unpacker self, int num_elements, object array_prop):
    cdef int n, bits
    n, bits = num_elements, 0

    while n:
      bits += 1
      n >>= 1

    cdef int count, i
    count = self.bitstream._read(bits)

    cdef object elements
    # Preallocate to be fast!
    elements = [None] * count

    for i in range(count):
      elements[i] = self._actually_unpack(array_prop)

    return elements

  cdef int64_t _unpack_int64(Unpacker self, uint64_t flags, int num_bits):
    if flags & ENCODEDAGAINSTTICKCOUNT:
      raise NotImplementedError('int64 cant be encoded against tickcount')

    cdef int negate, second_bits

    negate = 1
    second_bits = num_bits - 32

    if not (flags & UNSIGNED):
      second_bits -= 1
      if self.bitstream._read(1):
        negate = -1

    cdef uint64_t a, b
    a = self.bitstream._read(32)
    b = self.bitstream._read(second_bits)

    cdef int64_t value
    value = (a << 32) | b
    value *= negate

    return value

  def __iter__(self):
    try:
      while True:
        yield self._unpack()
    except unpacker.UnpackComplete:
      pass
